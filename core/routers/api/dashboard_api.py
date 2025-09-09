from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from app.database import async_session
from core.models.member import Members
from core.models.donation import Donation
from core.models.attendance import Attendance
from core.crud.user import UserCRUD


router = APIRouter()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_session)):
    total_members = (await db.execute(select(func.count()).select_from(Members))).scalar()
    total_donations = (await db.execute(select(func.sum(Donation.amount)))).scalar() or 0
    total_attendance = (await db.execute(select(func.count()).select_from(Attendance))).scalar()

    return {
        "total_members": total_members,
        "total_donations": total_donations,
        "total_attendance": total_attendance,
    }

@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_session)):
    user, member = UserCRUD.get_user_with_member(user.id, db)
    return {"user": user, "member": member}