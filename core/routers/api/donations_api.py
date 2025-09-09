from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from core.schemas.donation import DonationCreate, DonationUpdate, DonationRead
from core.models.donation import Donation, DonationType
from core.crud.donation import donation_crud
from app.database import async_session
from core.auth.deps import require_login, get_current_user_api
import uuid

router = APIRouter()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ------------------------
# List donations (API)
# ------------------------
@router.get("/", response_model=List[DonationRead])
async def list_donations(
    q: Optional[str] = Query(None),
    chapter_id: Optional[uuid.UUID] = Query(None),
    donation_type: Optional[DonationType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    dependencies=[Depends(get_current_user_api)],
    session: AsyncSession = Depends(get_session)
):
    # --- Convert empty strings to None ---
    chapter_id = chapter_id.strip() if chapter_id and chapter_id.strip() else None
    status = status.strip() if status and status.strip() else None

    # --- Parse UUID safely ---
    try:
        chapter_id_uuid = UUID(chapter_id) if chapter_id else None
    except ValueError:
        chapter_id_uuid = None

    # --- Parse Enum safely ---
    status_enum = None
    if status:
        try:
            status_enum = DonationStatus(status.lower())
        except ValueError:
            status_enum = None

    filters = {}
    if chapter_id_uuid:
        filters["chapter_id"] = chapter_id_uuid
    if status_enum:
        filters["status"] = status_enum

    stmt = donation_crud.select_stmt(
        q=q,
        filters=filters,
        search_fields=["first_name", "last_name", "email", "phone", "member_code"],
        page=page,
        page_size=page_size,
        order_by="created_at"
    )

    donations = (await session.execute(stmt)).scalars().all()
    return donations

# ------------------------
# Get single donation
# ------------------------
@router.get("/{donation_id}", response_model=DonationRead)
async def get_donation(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    donation = await donation_crud.get(session, member_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation

# ------------------------
# Create Donation
# ------------------------
@router.post("/", response_model=DonationRead)
async def create_donation(member_in: DonationCreate, session: AsyncSession = Depends(get_session)):
    return await donation_crud.create(session, member_in.model_dump())

# ------------------------
# Update Donation
# ------------------------
@router.patch("/{donation_id}", response_model=DonationRead)
async def update_donation(donation_id: uuid.UUID, donation_in: DonationUpdate, session: AsyncSession = Depends(get_session)):
    donation = await donation_crud.get(session, donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return await donation_crud.update(session, donation, donation_in.model_dump(exclude_unset=True))

# ------------------------
# Archive / Restore / Delete
# ------------------------
@router.post("/{donation_id}/archive", response_model=DonationRead)
async def archive_donation(donation_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    donation = await donation_crud.get(session, donation_id)
    return await donation_crud.update(session, donation, {"status": DonationStatus.inactive.value})

@router.post("/{donation_id}/restore", response_model=DonationRead)
async def restore_donation(donation_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    donation = await donation_crud.get(session, donation_id)
    return await donation_crud.update(session, donation, {"status": DonationStatus.active.value})

@router.delete("/{donation_id}")
async def delete_donation(donation_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    donation = await donation_crud.get(session, donation_id)
    await donation_crud.delete(session, donation)
    return {"detail": "Donation deleted successfully"}
