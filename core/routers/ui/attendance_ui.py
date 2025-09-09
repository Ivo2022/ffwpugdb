from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from datetime import date, datetime
from sqlalchemy.orm import selectinload
from core.models.member import Members  # make sure you import Member
from core.models.attendance import AttendanceStatus, Attendance
import uuid
from core.auth.deps import require_login
from core.crud.attendance import attendance_crud
from app.database import async_session
from utils.templates import templates

router = APIRouter(include_in_schema=False)

# Dependency to get async session
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# ------------------------
# List Attendance
# ------------------------
@router.get("/")
async def attendance_list(request: Request, date: Optional[str] = Query(None), q: Optional[str] = Query(None), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), user=Depends(require_login), session: AsyncSession = Depends(get_session),):
    if isinstance(user, RedirectResponse):
        return user

    # Prepare filters
    filters = {}
    if date:
        try:
            filters["attendance_date"] = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            filters["attendance_date"] = None

    # Build select statement (sync)
    stmt = attendance_crud.select_stmt(
        q=q,
        filters=filters,
        search_fields=["attendance_date", "member_name"],  # adjust fields for search
        page=page,
        page_size=page_size,
        order_by="attendance_date",
        descending=False,
    ).options(selectinload(Attendance.member)) 

    # Execute asynchronously
    attendance_list = (await session.execute(stmt)).scalars().all()

    # result = await session.execute(stmt)
    # attendance_list = result.scalars().all()

    # Count filtered total
    total = await attendance_crud.count_filtered(
        session,
        q=q,
        filters=filters,
        search_fields=["status", "member_name"],
    )

    # Group by date and summarize
    grouped_attendance = {}
    summary_by_date = {}
    for a in attendance_list:
        if not a.attendance_date:
            continue # skip if the date is missing
        key = a.attendance_date.strftime("%Y-%m-%d")
        if key not in grouped_attendance:
            grouped_attendance[key] = []
            summary_by_date[key] = {"present": 0, "online": 0, "excused": 0, "absent": 0}

        grouped_attendance[key].append(a)

        status = a.status.lower()
        if status == "present":
            summary_by_date[key]["present"] += 1
        elif status == "online":
            summary_by_date[key]["online"] += 1
        elif status == "excused":
            summary_by_date[key]["excused"] += 1
        else:
            summary_by_date[key]["absent"] += 1

    return templates.TemplateResponse(
        "/admin/attendance/list.html",
        {
            "request": request,
            "user": user, 
            "attendance_grouped": grouped_attendance,
            "summary_by_date": summary_by_date,
            "filter_date": date or "",
            "q": q or "",
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total // page_size) + (1 if total % page_size else 0),
        },
    )

# ------------------------
# Add Attendance Form
# ------------------------
@router.get("/create")
async def attendance_create_page(request: Request, user=Depends(require_login), session: AsyncSession = Depends(get_session)):
    if isinstance(user, RedirectResponse):
        return user
    
    # Fetch all members
    result = await session.execute(select(Members).order_by(Members.first_name))
    members = result.scalars().all()

    return templates.TemplateResponse(
        "/admin/attendance/create.html",
        {"request": request, "error": None, "members":members, "user": user, "attendance": None},
    )

# ------------------------
# Handle Attendance
# ------------------------
@router.post("/create", response_class=HTMLResponse, name="attendance_create")
async def create_attendance(
    request: Request,
    member_ids: list[str] = Form(...),
    attendance_date: date = Form(...),
    user=Depends(require_login),
    status: str = Form(...),
    remarks: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    if not member_ids:
        return templates.TemplateResponse(
            "/admin/attendance/create.html",
            {"request": request, "error": "No members selected"}
        )
    
    try:
        created_records = []

        for member_id in member_ids:
            obj_in = {
                "member_id": member_id,
                "attendance_date": attendance_date,
                "status": status,
                "remarks": remarks
            }
            record = await attendance_crud.create(session, obj_in)
            created_records.append(record)

        return RedirectResponse(url="/attendance", status_code=303)

    except Exception as e:
        return templates.TemplateResponse(
            "/admin/attendance/create.html",
            {
                "request": request,
                "error": str(e),
                "form_data": {
                    "member_ids": member_ids,
                    "attendance_date": attendance_date,
                    "status": status,
                    "remarks": remarks
                }
            }
        )


# -----------------------------
# Edit / Update Attendance Form
# -----------------------------
@router.get("/{attendance_id}/edit")
async def attendance_edit_page(request: Request, attendance_id: str, user=Depends(require_login), session: AsyncSession = Depends(get_session)):
    if isinstance(user, RedirectResponse):
        return user

    attendance = await attendance_crud.get(session, attendance_id, with_relationships=True)
    return templates.TemplateResponse(
        "/admin/attendance/update.html",
        {"request": request, "attendance": attendance},
    )

# ------------------------
# Edit / Update Attendance
# ------------------------
@router.post("/{attendance_id}/edit")
async def attendance_update(attendance_id: uuid.UUID, status: str = Form(...), attendance_date: date = Form(...), remarks: str = Form(...), session: AsyncSession = Depends(get_session), user=Depends(require_login),):
    if isinstance(user, RedirectResponse):
        return user

    attendance = await attendance_crud.get(session, attendance_id,  with_relationships=True)
    updates = {
        "status": status,
        "attendance_date": attendance_date,
        "remarks": remarks,
    }

    await attendance_crud.update(session, attendance, updates)
    return RedirectResponse(url="/attendance", status_code=303)

# ------------------------
# Search Attendance
# ------------------------
@router.get("/members/search")
async def search_members(q: str = Query(..., min_length=1), limit: int = Query(20, le=100), session: AsyncSession = Depends(get_session)):
    stmt = (
        select(Member)
        .where(
            or_(
                Member.first_name.ilike(f"%{q}%"),
                Member.last_name.ilike(f"%{q}%"),
                Member.member_code.ilike(f"%{q}%")
            )
        )
        .limit(limit)
    )
    result = await session.execute(stmt)
    members = result.scalars().all()

    return [{"id": m.id, "name": f"{m.first_name} {m.last_name}"} for m in members]
