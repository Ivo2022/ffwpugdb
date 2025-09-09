from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from core.schemas.member import MemberCreate, MemberUpdate, MemberRead
from core.models.member import Members, MemberStatus
from core.crud.member import member_crud
from app.database import async_session
from core.auth.dependencies import require_login
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
    chapter_id: Optional[uuid.UUID] = None,
    status: Optional[MemberStatus] = None,
    page: int = 1,
    page_size: int = 20,
    user=Depends(require_login),
    session: AsyncSession = Depends(get_session)
):
    filters = {}
    if chapter_id:
        filters["chapter_id"] = chapter_id
    if status:
        filters["status"] = status

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
