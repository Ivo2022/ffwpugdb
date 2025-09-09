from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import async_session
from core.models.member import Members, MemberStatus
from core.models.donation import Donation, DonationType
from core.models.attendance import Attendance, AttendanceStatus
from fastapi.templating import Jinja2Templates
from utils.templates import templates
from sqlalchemy.orm import selectinload

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.get("/dashboard")
async def dashboard_home(request: Request, db: AsyncSession = Depends(get_session)):
    # ---------- Members KPI Metrics ----------
    total_members = (await db.execute(select(func.count()).select_from(Members))).scalar()
    active_members = (await db.execute(select(func.count()).select_from(Members).where(Members.status == 'active'))).scalar()
    inactive_members = (await db.execute(select(func.count()).select_from(Members).where(Members.status == 'inactive'))).scalar()
    guest_members = (await db.execute(select(func.count()).select_from(Members).where(Members.status == 'guest'))).scalar()

    {MemberStatus.active}
    # Recent registrations (last 7)
    recent_members = (await db.execute(
        select(Members).order_by(desc(Members.created_at)).limit(7)
    )).scalars().all()

    # ---------- Donations KPI Metrics ----------
    total_donations = (await db.execute(select(func.sum(Donation.amount)))).scalar() or 0
    total_tithe = (await db.execute(
        select(func.sum(Donation.amount)).where(Donation.donation_type == "tithe")
    )).scalar() or 0
    total_sunday = (await db.execute(
        select(func.sum(Donation.amount)).where(Donation.donation_type == "sunday donation")
    )).scalar() or 0
    total_pledge = (await db.execute(
        select(func.sum(Donation.amount)).where(Donation.donation_type == "pledge")
    )).scalar() or 0

    # Recent donations (last 7)
    recent_donations = (await db.execute(
        select(Donation).options(selectinload(Donation.member)).order_by(desc(Donation.donation_date)).limit(7)
    )).scalars().all()
    
    # ---------- Attendance KPI Metrics ----------
    total_attendance = (await db.execute(select(func.count()).select_from(Attendance))).scalar() or 0
    total_present = (await db.execute(select(func.count()).where(Attendance.status == "present"))).scalar() or 0
    total_absent = (await db.execute(select(func.count()).where(Attendance.status == "absent"))).scalar() or 0

    # Recent attendance (last 7)
    recent_attendance = (await db.execute(
        select(Attendance).options(selectinload(Attendance.member)).order_by(desc(Attendance.attendance_date)).limit(7)
    )).scalars().all()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        # Members
        "total_members": total_members or 0,
        "active_members": active_members or 0,
        "inactive_members": inactive_members or 0,
        "recent_members": recent_members or 0,
        # Donations
        "recent_donations": recent_donations,
        "total_tithe": total_tithe,
        "total_sunday": total_sunday,
        "total_donations": total_donations,
        # Attendance
        "total_attendance": total_attendance,
        "total_present": total_present,
        "total_absent": total_absent,
        "recent_attendance": recent_attendance,

    })
