from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from core.models.member import MemberStatus, Members, Gender
from core.schemas.user import UserRead
from core.schemas.member import MemberCreate, MemberUpdate
from core.auth.deps import require_login, get_current_user
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from utils.templates import templates
from core.crud.member import member_crud
from typing import Optional
from uuid import UUID
from datetime import date
import uuid
from sqlmodel import select, Integer
from sqlalchemy import or_, func


router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ------------------------
# Read Members
# ------------------------

@router.get("/")
async def members_list(request: Request, q: Optional[str] = Query(None), chapter_id: Optional[str] = Query(None), status: Optional[str] = Query(None), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), user=Depends(require_login), session: AsyncSession = Depends(get_session),):
    if isinstance(user, RedirectResponse):
        return user

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

    members = (await session.execute(
        member_crud.select_stmt(
            q=q,
            filters=filters,
            search_fields=["first_name", "last_name", "email", "phone", "member_code"],
            page=page,
            page_size=page_size,
            order_by="created_at"
        )
    )).scalars().all()

    total = await member_crud.count_filtered(
        session,
        q=q,
        filters=filters,
        search_fields=["first_name", "last_name", "email", "phone", "member_code"]
    )

    return templates.TemplateResponse(
        "/admin/members/list.html",
        {
            "request": request,
            "user": user, 
            "members": members,
            "q": q or "",
            "selected_chapter": str(chapter_id_uuid) if chapter_id_uuid else "",
            "selected_status": status_enum.value if status_enum else "",
            "chapters": [],  # optional: add chapter list
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total // page_size) + (1 if total % page_size else 0),
        },
    )

# ------------------------
# Create Member
# ------------------------
@router.get("/create")
async def members_create_page(request: Request, user=Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("/admin/members/create.html", {"request": request, "member": None, "user": user, "error": None})

@router.post("/create", response_class=HTMLResponse)
async def members_create(request: Request, member_code: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), email: Optional[str] = Form(None), phone: Optional[str] = Form(None), session: AsyncSession = Depends(get_session)):
    member_in = {
        "member_code": member_code,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone
    }
    try:
        member = await member_crud.create(session, member_in)
        return RedirectResponse(url="/members", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "/admin/members/create.html",
            {"request": request, "error": str(e), "member": member_in}
        )

"""
async def generate_member_code(db: AsyncSession) -> str:
    result = await db.execute(select(Members.member_code))
    codes = result.scalars().all()

    if not codes:
        return "MEM0001"

    # extract numeric part and find max
    numbers = [
        int(code.replace("MEM", "")) for code in codes if code and code.startswith("MEM")
    ]
    next_num = max(numbers) + 1 if numbers else 1
    return f"MEM{next_num:04d}"
"""

async def generate_member_code(db: AsyncSession) -> str:
    """
    Generates the next member code in the format MEM0001, MEM0002, etc.
    Uses database to get the current max to avoid fetching all codes.
    """
    # Get the maximum numeric part of existing member codes
    result = await db.execute(
        select(func.max(func.cast(func.substring(Members.member_code, 4), Integer)))
    )
    max_num = result.scalar()  # None if no members exist yet

    next_num = (max_num or 0) + 1
    return f"MEM{next_num:04d}"

#----------------------------
# Profile Editing
#----------------------------
@router.get("/profile/edit")
async def edit_profile_get(
    request: Request,
    # user: UserRead = Depends(get_current_user),
    user: UserRead = Depends(get_current_user),
    # user=Depends(require_login),
    db: AsyncSession = Depends(get_session),
):
    # Load member info if exists
    user_id: UUID = user.id  # make sure it's a UUID type
    member_query = select(Members).where(Members.user_id == UUID(str(user.id)))
    result = await db.execute(member_query)
    member = result.scalar_one_or_none()

    return templates.TemplateResponse(
        "/admin/members/profile.html",
        {"request": request, "user": user, "member": member},
    )

@router.post("/profile/edit")
async def edit_profile_post(
    request: Request,
    user: UserRead = Depends(get_current_user),
    first_name: str = Form(...),
    last_name: str = Form(...),
    other_names: str = Form(None),
    gender: Gender = Form(...),
    phone: str = Form(None),
    email: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    user_id = UUID(str(user.id))  # convert to UUID

    # Check if member exists
    member_query = select(Members).where(Members.user_id == user_id)
    result = await db.execute(member_query)
    member = result.scalar_one_or_none()

    try:
                # Create member with generated member_code
        for _ in range(5):  # retry up to 5 times in case of collision
            try:
                member = Members(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    member_code=await generate_member_code(db),
                    first_name=first_name,
                    last_name=last_name,
                    other_names=other_names,
                    phone=phone,
                    gender=gender,
                    email=email,
                    status=MemberStatus.active.value,
                    join_date=date.today(),
                )
                db.add(member)
                await db.commit()
                await db.refresh(member)
                break
            except IntegrityError as e:
                await db.rollback()
                # If it's a duplicate member_code, retry
                if "members_member_code_key" in str(e.orig):
                    continue
                # Otherwise, raise
                raise e

    except IntegrityError as e:
        await db.rollback()

        # Detect which constraint failed
        error_message = "An unexpected error occurred."
        if 'members_phone_key' in str(e.orig):
            error_message = "This phone number is already registered."
        elif 'members_email_key' in str(e.orig):
            error_message = "This email is already registered."
        elif 'members_member_code_key' in str(e.orig):
            error_message = "Member code conflict, please try again."

        # Return the template with error
        return templates.TemplateResponse(
            "profile_edit.html",
            {
                "request": request,
                "member": member,
                "user": user,
                "error": error_message
            },
            status_code=400,
        )

    # Redirect based on role
    if "admin" in user.role_names:
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    elif "staff" in user.role_names:
        return RedirectResponse(url="/staff/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/member/dashboard", status_code=303)

# ------------------------
# Edit / Update
# ------------------------
@router.get("/{member_id}/edit")
async def members_edit_page(request: Request, member_id: uuid.UUID, user=Depends(require_login), session: AsyncSession = Depends(get_session)):
    if isinstance(user, RedirectResponse):
        return user
    member = await member_crud.get(session, member_id)
    return templates.TemplateResponse("/admin/members/update.html", {"request": request, "user": user, "member": member})

@router.post("/{member_id}/edit")
async def members_update(request: Request, member_id: uuid.UUID, member_code: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), email: Optional[str] = Form(None), phone: Optional[str] = Form(None), status: Optional[str] = Form(None), session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    updates = {
        "member_code": member_code,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "status": status,
    }
    await member_crud.update(session, member, updates)
    return RedirectResponse(url="/members", status_code=303)

# ------------------------
# Archive / Restore / Delete
# ------------------------
@router.post("/{member_id}/archive")
async def members_archive(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    await member_crud.update(session, member, {"status": MemberStatus.inactive.value})
    return RedirectResponse(url="/members", status_code=303)

@router.post("/{member_id}/restore")
async def members_restore(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    await member_crud.update(session, member, {"status": MemberStatus.active.value})
    return RedirectResponse(url="/members", status_code=303)

@router.post("/{member_id}/delete")
async def members_delete(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    member = await member_crud.get(session, member_id)
    await member_crud.delete(session, member)
    return RedirectResponse(url="/members", status_code=303)
