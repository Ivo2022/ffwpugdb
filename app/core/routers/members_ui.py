from fastapi import APIRouter, Request, Form, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from app.database import async_session
from core.models.member import Members, MemberStatus
from core.crud import member as crud_members
from core.auth.deps import require_login
from utils.templates import templates

import uuid

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# --------------------
# --- List Members ---
# --------------------
@router.get("/")
async def members_list(request: Request, q: Optional[str] = Query(None), chapter_id: Optional[uuid.UUID] = Query(None), status: Optional[MemberStatus] = Query(None), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), user = Depends(require_login), session: AsyncSession = Depends(get_session),):
    if isinstance(user, RedirectResponse):
        return user

    members, total = await crud_members.get_members(session, q, chapter_id, status, page, page_size)

    return templates.TemplateResponse(
        "/admin/members/list.html",
        {
            "request": request,
            "members": members,
            "q": q or "",
            "selected_chapter": str(chapter_id) if chapter_id else "",
            "selected_status": status.value if status else "",
            "chapters": [],
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total // page_size) + (1 if total % page_size else 0),
        },
    )

# --------------------------
# --- Create Member Page ---
# --------------------------
@router.get("/create")
async def members_create_page(request: Request, user=Depends(require_login),):
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "/admin/members/create.html",
        {"request": request, "member": None, "error": None},
    )

# --------------------------
# --- Handle Create Form ---
# --------------------------
@router.post("/create", response_class=HTMLResponse)
async def members_create(request: Request, member_code: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), email: EmailStr = Form(None), session: AsyncSession = Depends(get_session),):
    member = Members(
        member_code=member_code,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )

    created_member, error_message = await crud_members.create_member(session, member)

    if error_message:
        return templates.TemplateResponse(
            "/admin/members/create.html",
            {"request": request, "error": error_message, "member": member},
        )

    return RedirectResponse(url="/members", status_code=303)

# --------------------------
# --- Update Member Page ---
# --------------------------
@router.get("/{member_id}/edit")
async def members_edit_page(request: Request, member_id: uuid.UUID, user=Depends(require_login), session: AsyncSession = Depends(get_session),):
    if isinstance(user, RedirectResponse):
        return user

    member = await crud_members.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    return templates.TemplateResponse(
        "/admin/members/update.html", {"request": request, "member": member}
    )

# --------------------------
# --- Handle Update Form ---
# --------------------------
@router.post("/{member_id}/edit")
async def members_update(request: Request, member_id: uuid.UUID, member_code: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), email: str = Form(None),  phone: str = Form(None), session: AsyncSession = Depends(get_session),):
    member = await crud_members.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.first_name = first_name
    member.last_name = last_name
    member.member_code = member_code
    member.email = email
    member.phone = phone

    await crud_members.update_member(session, member)
    return RedirectResponse(url="/members", status_code=303)

# --------------------------
# --- Delete Member --------
# --------------------------
@router.post("/{member_id}/delete")
async def members_delete(member_id: uuid.UUID, session: AsyncSession = Depends(get_session),):
    member = await crud_members.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await crud_members.delete_member(session, member)
    return RedirectResponse(url="/members", status_code=303)
 
# --------------------------
# --- Archive Member -------
# --------------------------
@router.post("/{member_id}/archive")
async def members_archive(member_id: uuid.UUID, session: AsyncSession = Depends(get_session),):
    member = await crud_members.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await crud_members.archive_member(session, member)
    return RedirectResponse(url="/members", status_code=303)

# --------------------------
# --- Restore Member -------
# --------------------------
@router.post("/{member_id}/restore")
async def members_restore(member_id: uuid.UUID, session: AsyncSession = Depends(get_session),):
    member = await crud_members.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await crud_members.restore_member(session, member)
    return RedirectResponse(url="/members", status_code=303)
