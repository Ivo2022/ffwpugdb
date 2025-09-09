from fastapi import APIRouter, FastAPI, Request, Depends, Query, Form
from fastapi.staticfiles import StaticFiles
from utils.templates import templates
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from core.models.donation import Donation, DonationType
from core.models.user import User
from typing import Optional
from datetime import datetime, date
import uuid
from sqlmodel import select
from sqlalchemy import or_, func
from core.auth.deps import require_roles

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ----- List donations -----
@router.get("/")
async def donations_list(
    request: Request,
    q: Optional[str] = Query(None),
    member_id: Optional[uuid.UUID] = Query(None),
    donation_type: Optional[DonationType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Donation)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                func.lower(Donation.amount).like(func.lower(like)),
                func.lower(Donation.donation_type).like(func.lower(like)),
                func.lower(Donation.date).like(func.lower(like))
            )
        )
    if member_id:
        stmt = stmt.where(Donation.member_id == member_id)
    if donation_type:
        stmt = stmt.where(Donation.donation_type == donation_type)

    # total count (optional)
    count_stmt = stmt.with_only_columns(func.count()).order_by(None)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Donation.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    donations = (await session.execute(stmt)).scalars().all()

    # Chapters dropdown (optional). If you have a Chapter model, query names here.
    # chapters = (await session.execute(select(Chapter.id, Chapter.name).order_by(Chapter.name))).all()
    members = []  # fallback if Chapter not yet ready

    return templates.TemplateResponse(
        "/admin/donation/donation.html",
        {
            "request": request,
            "members": donations,
            "q": q or "",
            "selected_chapter": str(chapter_id) if chapter_id else "",
            "selected_donation_type": donation_type.value if donation_type else "",
            "members": members,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total // page_size) + (1 if total % page_size else 0),
        },
    )

# --- Create Member Page ---
@router.get("/create")
async def members_create_page(request: Request):
    return templates.TemplateResponse("/admin/members/create.html", {"request": request})

# --- Handle Create Form Submission ---
@router.post("/create")
async def members_create(
    request: Request,
    member_code: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(None),
    session: AsyncSession = Depends(get_session)
):
    new_member = Members(
        member_code=member_code,
        first_name=first_name,
        last_name=last_name,
        email=email
    )
    session.add(new_member)
    await session.commit()
    await session.refresh(new_member)
    return RedirectResponse(url="/members", status_code=303)

# --- Update Member Page ---
@router.get("/{member_id}/edit")
async def members_edit_page(request: Request, member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await session.get(Members, member_id)
    return templates.TemplateResponse("/admin/members/update.html", {"request": request, "member": member})

# --- Handle Update Form ---
@router.post("/{member_id}/edit")
async def members_update(
    request: Request,
    member_id: uuid.UUID,
    member_code: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(None),
    session: AsyncSession = Depends(get_session)
):
    member = await session.get(Members, member_id)
    member.first_name = first_name
    member.last_name = last_name
    member.member_code = member_code
    member.email = email
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return RedirectResponse(url="/members", status_code=303)


# --- Delete Member ---
@router.post("/{member_id}/delete")
async def members_delete(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    # Fetch the object in the current session
    statement = select(Members).where(Members.id == member_id)
    result = await session.execute(statement)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Delete using session.delete
    await session.delete(member)
    await session.commit()

    return RedirectResponse(url="/members", status_code=303)


@router.post("/{member_id}/archive")
async def members_archive(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    # Fetch member
    statement = select(Members).where(Members.id == member_id)
    result = await session.execute(statement)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Soft delete: set status to 'inactive' or 'archived'
    member.status = "inactive"
    session.add(member)
    await session.commit()

    return RedirectResponse(url="/members", status_code=303)

@router.post("/{member_id}/restore")
async def members_restore(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await session.get(Members, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.status = MemberStatus.active
    session.add(member)
    await session.commit()
    return RedirectResponse(url="/members", status_code=303)

@router.get("/member/dashboard")
async def member_dashboard(
    request: Request,
    user: User = Depends(require_roles("member")),
    db: AsyncSession = Depends(get_session)
):
    # Get their donations
    donations = (await db.execute(
        select(Donation).where(Donation.member_id == user.id).order_by(desc(Donation.donation_date))
    )).scalars().all()

    # Get their attendance
    attendance = (await db.execute(
        select(Attendance).where(Attendance.member_id == user.id).order_by(desc(Attendance.attendance_date))
    )).scalars().all()

    return templates.TemplateResponse("admin/members/dashboard.html", {
        "request": request,
        "user": user,
        "donations": donations,
        "attendance": attendance,
    })

@router.get("/staff/dashboard")
async def staff_dashboard(
    request: Request,
    user: User = Depends(require_roles("staff")),
    db: AsyncSession = Depends(get_session)
):
    # Get their donations
    donations = (await db.execute(
        select(Donation).where(Donation.member_id == user.id).order_by(desc(Donation.donation_date))
    )).scalars().all()

    # Get their attendance
    attendance = (await db.execute(
        select(Attendance).where(Attendance.member_id == user.id).order_by(desc(Attendance.attendance_date))
    )).scalars().all()

    return templates.TemplateResponse("/admin/staff/dashboard.html", {
        "request": request,
        "user": user,
        "donations": donations,
        "attendance": attendance,
    })