from fastapi import APIRouter, Request, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func, desc
from datetime import date, datetime
from app.database import async_session
from utils.templates import templates
from core.models.member import Members
from core.models.donation import Donation
from core.models.attendance import Attendance
from core.models.user import User
from core.auth.deps import get_current_user, require_roles
from core.crud.user import UserCRUD
from uuid import UUID
from sqlalchemy.orm import selectinload

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

#-----------------------------
# ADMIN DASHBOARD SECTION
#-----------------------------
@router.get("/admin/dashboard")
async def admin_dashboard(request: Request, user: User = Depends(require_roles("admin")), db: AsyncSession = Depends(get_session),):
    #----------------
    # Personal info
    #----------------
    result = await db.execute(select(Members).where(Members.user_id == UUID(str(user.id))))
    personal_info = result.scalar_one_or_none()

    #-----------------
    # Everything else
    #-----------------
    # Donations KPIs
    donations = (await db.execute(select(Donation).order_by(desc(Donation.donation_date)))).scalars().all()
    total_donations = (await db.execute(select(func.sum(Donation.amount)))).scalar() or 0
    total_tithe = (await db.execute(select(func.sum(Donation.amount)).where(Donation.donation_type == "tithe"))).scalar() or 0
    total_sunday = (await db.execute(select(func.sum(Donation.amount)).where(Donation.donation_type == "sunday donation"))).scalar() or 0
    total_pledge = (await db.execute(select(func.sum(Donation.amount)).where(Donation.donation_type == "pledge"))).scalar() or 0
    recent_donations = (await db.execute(select(Donation).options(selectinload(Donation.member)).order_by(desc(Donation.donation_date)).limit(7))).scalars().all()

    # Members KPIs
    total_members = (await db.execute(select(func.count()).select_from(Members))).scalar()
    active_members = (await db.execute(select(func.count()).select_from(Members).where(Members.status == 'active'))).scalar()
    guest_members = (await db.execute(select(func.count()).select_from(Members).where(Members.status == 'guest'))).scalar()
    recent_members = (await db.execute(select(Members).order_by(desc(Members.created_at)).limit(5))).scalars().all()

    # Attendance KPIs
    attendance = (await db.execute(select(Attendance).order_by(desc(Attendance.attendance_date)))).scalars().all()
    today = date.today()
    attendance_today = (await db.execute(select(func.count()).where(Attendance.attendance_date == today))).scalar() or 0
    present_today = (await db.execute(select(func.count()).where(Attendance.attendance_date == today, Attendance.status == 'present')
    )).scalar() or 0
    absent_today = (await db.execute(select(func.count()).where(Attendance.attendance_date == today, Attendance.status == 'absent')
    )).scalar() or 0

    total_attendance = (await db.execute(select(func.count()).select_from(Attendance))).scalar() or 0
    total_present = (await db.execute(select(func.count()).where(Attendance.status == "present"))).scalar() or 0
    total_absent = (await db.execute(select(func.count()).where(Attendance.status == "absent"))).scalar() or 0
    recent_attendance = (await db.execute(select(Attendance).options(selectinload(Attendance.member)).order_by(desc(Attendance.id)).limit(10))).scalars().all()

    return templates.TemplateResponse("/admin/dashboard.html",
        {
            "request": request,
            "user": user,
            "personal_info": personal_info,
            "donations": donations,
            "total_attendance": total_attendance,
            "total_present": total_present,
            "total_absent": total_absent,
            "recent_attendance": recent_attendance,
            "total_members": total_members,
            "active_members": active_members,
            "guest_members": guest_members,
            "present_today": present_today,
            "absent_today": absent_today,
            "total_donations": total_donations,
            "recent_members": recent_members,
            "recent_donations": recent_donations,
            "total_tithe": total_tithe,
            "total_sunday": total_sunday,
        },
    )

"""
STAFF DASHBOARD
@router.get("/staff/dashboard")
async def staff_dashboard(
    request: Request,
    user: User = Depends(require_roles("staff")),
    session: AsyncSession = Depends(get_session)
):
    attendance = (await session.execute(
        select(Attendance).where(Attendance.member_id == user.id).order_by(desc(Attendance.attendance_date))
    )).scalars().all()

    return templates.TemplateResponse("/admin/staff/dashboard.html", {
        "request": request,
        "user": user,
        "attendance": attendance
    })

@router.get("/staff/dashboard")
async def staff_dashboard(
    request: Request,
    user: User = Depends(require_roles("staff")),
    db: AsyncSession = Depends(get_session),
):
    donations = (
        await db.execute(
            select(Donation).order_by(desc(Donation.donation_date))
        )
    ).scalars().all()

    attendance = (
        await db.execute(
            select(Attendance).order_by(desc(Attendance.attendance_date))
        )
    ).scalars().all()

    return templates.TemplateResponse(
        "/admin/staff/dashboard.html",
        {
            "request": request,
            "user": user,
            "donations": donations,
            "attendance": attendance,
        },
    )
"""

#-----------------------------
# STAFF DASHBOARD SECTION
#-----------------------------
@router.get("/staff/dashboard")
async def staff_dashboard(
    request: Request,
    user: User = Depends(require_roles("staff")),
    db: AsyncSession = Depends(get_session),
):
    # Check if member exists
    user_id = UUID(str(user.id))  # convert to UUID
    member_query = select(Members).where(Members.user_id == user_id)
    result = await db.execute(member_query)
    member = result.scalar_one_or_none()

    # 2️⃣ Get department-specific info
    # Assume Staff model has department_id
    result = await db.execute(
        select(Donation)
        # .where(Donation.department_id == user.department_id)  # filter by department
        .order_by(desc(Donation.donation_date))
    )
    donations = result.scalars().all()

    result = await db.execute(
        select(Attendance)
        # .where(Attendance.department_id == user.department_id)  # filter by department
        .order_by(desc(Attendance.attendance_date))
    )
    attendance = result.scalars().all()

    roles = []
    # if your User model has is_admin, is_staff, etc.
    if getattr(user, "is_admin", False):
        roles.append("admin")
    if getattr(user, "is_staff", False):
        roles.append("staff")
    if getattr(user, "is_member", False):
        roles.append("member")
    
    return templates.TemplateResponse(
        "/admin/staff/dashboard.html",
        {
            "request": request,
            "user": user,
            "donations": donations,
            "attendance": attendance,
            "roles": roles,
            "member": member,
        },
    )

#-----------------------------
# MEMBER DASHBOARD SECTION
#-----------------------------
@router.get("/member/dashboard")
async def member_dashboard(request: Request, user: User = Depends(require_roles("member", "staff", "admin")), db: AsyncSession = Depends(get_session),):
    user_id = UUID(str(user.id))  # convert to UUID

    # Check if member exists
    member_query = select(Members).where(Members.user_id == user_id)
    result = await db.execute(member_query)
    member = result.scalar_one_or_none()

    donations = (await db.execute(select(Donation).where(Donation.member_id == member.id).order_by(desc(Donation.donation_date)))).scalars().all()
    attendance = (await db.execute(select(Attendance).where(Attendance.member_id == member.id).order_by(desc(Attendance.attendance_date)))).scalars().all()
    
    return templates.TemplateResponse(
        "/admin/members/dashboard.html",
        {
            "request": request,
            "user": user,
            "member": member,
            "donations": donations,
            "attendance": attendance,
        },
    )
