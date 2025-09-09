from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from core.schemas.member import MemberCreate, MemberUpdate, MemberRead
from core.models.member import Members, MemberStatus
from core.crud.member import member_crud
from app.database import async_session
from core.auth.deps import require_login, get_current_user_api
import uuid

router = APIRouter()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ------------------------
# List Members (API)
# ------------------------
@router.get("/", response_model=List[MemberRead])
async def list_members(
    q: Optional[str] = Query(None),
    chapter_id: Optional[uuid.UUID] = Query(None),
    status: Optional[MemberStatus] = Query(None),
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
            status_enum = MemberStatus(status.lower())
        except ValueError:
            status_enum = None

    filters = {}
    if chapter_id_uuid:
        filters["chapter_id"] = chapter_id_uuid
    if status_enum:
        filters["status"] = status_enum

    stmt = member_crud.select_stmt(
        q=q,
        filters=filters,
        search_fields=["first_name", "last_name", "email", "phone", "member_code"],
        page=page,
        page_size=page_size,
        order_by="created_at"
    )

    members = (await session.execute(stmt)).scalars().all()
    return members

# ------------------------
# Get single member
# ------------------------
@router.get("/{member_id}", response_model=MemberRead)
async def get_member(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

# ------------------------
# Create Member
# ------------------------
@router.post("/", response_model=MemberRead)
async def create_member(member_in: MemberCreate, session: AsyncSession = Depends(get_session)):
    return await member_crud.create(session, member_in.model_dump())

# ------------------------
# Update Member
# ------------------------
@router.patch("/{member_id}", response_model=MemberRead)
async def update_member(member_id: uuid.UUID, member_in: MemberUpdate, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return await member_crud.update(session, member, member_in.model_dump(exclude_unset=True))

# ------------------------
# Archive / Restore / Delete
# ------------------------
@router.post("/{member_id}/archive", response_model=MemberRead)
async def archive_member(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    return await member_crud.update(session, member, {"status": MemberStatus.inactive.value})

@router.post("/{member_id}/restore", response_model=MemberRead)
async def restore_member(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    return await member_crud.update(session, member, {"status": MemberStatus.active.value})

@router.delete("/{member_id}")
async def delete_member(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    await member_crud.delete(session, member)
    return {"detail": "Member deleted successfully"}
"""
# ------------------------
# Search Attendance
# ------------------------
@router.get("/members/search")
async def search_members(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, le=100),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Members).where(
        (Members.first_name.ilike(f"%{q}%")) | (Members.last_name.ilike(f"%{q}%"))
    ).limit(limit)

    result = await session.execute(stmt)
    members = result.scalars().all()

    return [
        {"id": m.id, "name": f"{m.first_name} {m.last_name}"}
        for m in members
    ]
"""