# core/routers/donation.py
from fastapi import APIRouter, Depends
from core.crud.donation import create_donation, get_donations_by_member
from core.schemas.donation import DonationCreate, DonationRead
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from core.models.donation import Donation

router = APIRouter(prefix="/donations", tags=["Donations"])

# Dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/", response_model=DonationRead)
async def add_donation(donation: DonationCreate, db: AsyncSession = Depends(get_session)):
    don_obj = Donation(**donation.dict())
    return await create_donation(db, don_obj)

@router.get("/{member_id}", response_model=list[DonationRead])
async def list_donations(member_id: str, db: AsyncSession = Depends(get_session)):
    return await get_donations_by_member(db, member_id)
