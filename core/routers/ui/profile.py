"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import select
from app.database import get_session
from app.models.user import User
from app.models.member import Members
from app.auth.deps import get_current_user

router = APIRouter()

@router.get("/profile/edit")
async def edit_profile_ui(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Fetch member record if exists
    result = await session.execute(select(Members).where(Members.user_id == user.id))
    member = result.scalar_one_or_none()
    return templates.TemplateResponse(
        "/profile/edit.html",
        {"request": request, "user": user, "member": member},
    )

@router.post("/profile/edit")
async def edit_profile(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(None),
    dob: str = Form(None),  # optional fields
    address: str = Form(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check if a member record already exists
    result = await session.execute(select(Members).where(Members.user_id == user.id))
    member = result.scalar_one_or_none()

    if member:
        # Update existing member
        member.first_name = first_name
        member.last_name = last_name
        member.phone = phone
        member.dob = dob
        member.address = address
    else:
        # Create new member linked to this user
        member = Members(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            dob=dob,
            address=address,
        )
        session.add(member)

    await session.commit()
    await session.refresh(member)

    return RedirectResponse(url="/dashboard", status_code=303)
"""