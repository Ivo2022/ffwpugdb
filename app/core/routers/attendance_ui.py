# ------------------------------
# ATTENDANCE UI for managing Jinja2 Templates UIs
# Written on this date, 01-09-2025
# ------------------------------

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from core.schemas.attendance import AttendanceCreate
from core.models.member import Members
from core.models.attendance import Attendance
from utils.templates import templates
from uuid import UUID
from typing import List
from core.models.event_session import EventSession  # ✅ import this
from datetime import date, datetime

router = APIRouter(include_in_schema=False)

# ------------------------------
# DB Session
# ------------------------------
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ------------------------------
# List Attendance
# ------------------------------
@router.get("/", name="attendance_list")
async def list_attendance(request: Request, db: AsyncSession = Depends(get_session)):
    # Get all attendance records
    result = await db.exec(select(Attendance))
    attendance_records = result.all()

    # Attach member info to each attendance
    attendance_with_members = []
    for a in attendance_records:
        member = await db.get(Members, a.member_id)
        attendance_with_members.append({
            "id": a.id,
            "member_id": member.member_code,
            "member_name": f"{member.first_name} {member.last_name}" if member else "N/A",
            "attendance_date": a.attendance_date,
            "status": a.status,
            "remarks": a.remarks
        })

    return templates.TemplateResponse(
        "admin/attendance/list.html",
        {"request": request, "attendance": attendance_with_members}
    )

# ------------------------------
# Create Attendance Page
# ------------------------------
@router.get("/create", name="attendance_create_form")
async def create_attendance_form(request: Request, db: AsyncSession = Depends(get_session)):
    # Get all members
    result = await db.exec(select(Members))
    members = result.all()

    return templates.TemplateResponse(
        "admin/attendance/create.html",
        {"request": request, "members": members}
    )

# ------------------------------
# Handle Create Form Submission
# ------------------------------
@router.post("/create", name="attendance_create")
async def create_attendance(request: Request, attendance_date: date = Form(...), status: str = Form(...), remarks: str = Form(""), member_ids: list[UUID] = Form(...), db: AsyncSession = Depends(get_session)):
    for member_id in member_ids:
        attendance = Attendance(
            member_id=member_id,
            attendance_date=attendance_date,
            status=status,
            remarks=remarks
        )
        db.add(attendance)

    await db.commit()
    return RedirectResponse(url=router.url_path_for("/attendance"), status_code=303)

# ------------------------------
# GET - Load Update Attendance Form
# ------------------------------
"""
@router.get("/update/{attendance_id}", name="attendance_update")
async def update_attendance_form(attendance_id: UUID, request: Request, db: AsyncSession = Depends(get_session)):
    attendance = db.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")
    results = await db.exec(select(Members))
    members_results = results.all()
    return templates.TemplateResponse(
        "admin/attendance/update.html",
        {"request": request, "attendance": attendance, "members": members_results}
    )
"""
# -----------------------------
# GET - load edit form
# -----------------------------
@router.get("/update/{attendance_id}", name="attendance_update")
async def edit_attendance_form(request: Request, attendance_id: UUID, session: AsyncSession = Depends(get_session)):
    stmt = select(Attendance).where(Attendance.id == attendance_id)
    result = await session.execute(stmt)
    attendance = result.scalar_one_or_none()
    if not attendance:
        return RedirectResponse(url="/attendance", status_code=302)

    # Example: fetch members for dropdown
    # inside your GET route
    result = await session.execute(select(Members))
    members = result.scalars().all()

    return templates.TemplateResponse(
        "admin/attendance/update.html",
        {
            "request": request,
            "attendance": attendance,
            "members": members
        }
    )

"""
@router.post("/update/{attendance_id}", name="attendance_update")
async def update_attendance(
    request: Request,
    attendance_id: UUID,
    member_id: UUID,
    attendance_date: date = Form(...),
    status: str = Form(...),
    db: AsyncSession = Depends(get_session)
):
    attendance = await db.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")
    attendance.member_id = member_id
    attendance.attendance_date = attendance_date
    attendance.status = status
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return RedirectResponse(url=request.url_for("attendance_list"), status_code=303)
"""

# -----------------------------
# POST - update attendance
# -----------------------------
@router.post("/update/{attendance_id}")
async def update_attendance(attendance_id: UUID, member_id: UUID = Form(...), attendance_date: date = Form(...), status: str = Form(...), remarks: str = Form(None), session: AsyncSession = Depends(get_session),):
    # Parse date string into a proper date object
    # date_obj = datetime.strptime(attendance_date, "%Y-%m-%d").date()

    stmt = select(Attendance).where(Attendance.id == attendance_id)
    result = await session.execute(stmt)
    attendance = result.scalar_one_or_none()

    if not attendance:
        return RedirectResponse(url="/attendance", status_code=302)

    # Update fields
    attendance.member_id = member_id
    attendance.attendance_date = attendance_date
    attendance.status = status
    attendance.remarks = remarks

    session.add(attendance)
    await session.commit()
    await session.refresh(attendance)

    # Redirect back to list or details page
    return RedirectResponse(url="/attendance", status_code=302)

# ------------------------------
# Delete Attendance
# ------------------------------
@router.get("/delete/{attendance_id}", name="attendance_delete")
def delete_attendance(attendance_id: str, request: Request, db: Session = Depends(get_session)):
    attendance = db.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")
    db.delete(attendance)
    db.commit()
    return RedirectResponse(url=request.url_for("attendance_list"), status_code=303)

# ------------------------------
# Insert More than one Attendants
# ------------------------------
@router.post("/mark")
async def mark_attendance(
    request: Request,
    member_ids: List[UUID] = Form(...),   # ✅ Accept UUIDs from form checkboxes
    status: str = Form("present"),
    remarks: str = Form(None),
    db: Session = Depends(get_session)
):
    for member_id in member_ids:
        attendance = models.Attendance(
            member_id=member_id,
            status=status,
            remarks=remarks
        )
        db.add(attendance)
    db.commit()
    return {"success": True, "marked": len(member_ids)}

@router.post("/attendance/record/")
async def record_attendance(
    session_id: str = Form(...),
    member_ids: list[str] = Form(...),   # multiple members from checkboxes
    remarks: str = Form(""),
    db: AsyncSession = Depends(get_session)
):
    for mid in member_ids:
        attendance = Attendance(
            session_id=session_id,
            member_id=mid,
            remarks=remarks,
            status="present"
        )
        db.add(attendance)
    await db.commit()
    return {"message": f"Recorded attendance for {len(member_ids)} members"}


@router.post("/")
async def mark_attendance(data: AttendanceCreate, db: AsyncSession = Depends(get_session)):
    records = await create_attendance(
        session=db,
        session_id=data.session_id,
        member_ids=data.member_ids,
        status=data.status,
        remarks=data.remarks
    )
    return {"success": True, "saved": len(records)}