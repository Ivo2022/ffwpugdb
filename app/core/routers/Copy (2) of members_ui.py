from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import RedirectResponse
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from core.models.member import Members, MemberStatus
from typing import List, Optional
from utils.templates import templates
from sqlmodel import select
from sqlalchemy import or_, func
import uuid

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# --- List Members ---
"""
@router.get("/")
async def members_list(request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.exec(Members.select())
    members: List[Member] = result.all()
    return templates.TemplateResponse("admin/members/list.html", {"request": request, "members": members})
"""
@router.get("/")
async def members_list(
    request: Request,
    q: Optional[str] = Query(None),
    chapter_id: Optional[uuid.UUID] = Query(None),
    status: Optional[MemberStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Members)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                func.lower(Members.first_name).like(func.lower(like)),
                func.lower(Members.last_name).like(func.lower(like)),
                func.lower(Members.email).like(func.lower(like)),
                func.lower(Members.phone).like(func.lower(like)),
                func.lower(Members.member_code).like(func.lower(like)),
            )
        )
    if chapter_id:
        stmt = stmt.where(Members.chapter_id == chapter_id)
    if status:
        stmt = stmt.where(Members.status == status)

    # total count (optional)
    count_stmt = stmt.with_only_columns(func.count()).order_by(None)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Members.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    members = (await session.execute(stmt)).scalars().all()

    # Chapters dropdown (optional). If you have a Chapter model, query names here.
    # chapters = (await session.execute(select(Chapter.id, Chapter.name).order_by(Chapter.name))).all()
    chapters = []  # fallback if Chapter not yet ready

    return templates.TemplateResponse(
        "/admin/members/list.html",
        {
            "request": request,
            "members": members,
            "q": q or "",
            "selected_chapter": str(chapter_id) if chapter_id else "",
            "selected_status": status.value if status else "",
            "chapters": chapters,
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