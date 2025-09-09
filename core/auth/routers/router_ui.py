from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import date, datetime
from app.database import async_session
from core.models.user import User  # ✅ change this import to match your project
from core.auth.jwt_handler import create_access_token, decode_access_token
from core.auth.password_utils import verify_password, get_password_hash
from utils.templates import templates
from core.models.user import User, Role, UserRole  # ✅ change this import to match your project
from core.models.member import MemberStatus
import uuid

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# -----------------------------
# LOGIN (UI)
# -----------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("/admin/auth/login.html", {"request": request})

"""
@router.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "/admin/auth/login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=400,
        )

    # ✅ Create JWT + store session
    access_token = create_access_token({"sub": str(user.id)})
    request.session["user_id"] = str(user.id)
    request.session["token"] = access_token

    return RedirectResponse(url="/dashboard", status_code=303)
"""

@router.post("/login")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...), session: AsyncSession = Depends(get_session),):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "/admin/auth/login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=400,
        )

    # ✅ Create JWT + store session
    access_token = create_access_token({"sub": str(user.id)})
    request.session["user_id"] = str(user.id)
    request.session["token"] = access_token

    # ✅ Get user roles
    roles_query = await session.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    user_roles = [r[0] for r in roles_query.fetchall()]
    
    # ✅ Redirect based on role
    if "admin" in user_roles:
        redirect_url = "/admin/dashboard"
    elif "member" in user_roles:
        redirect_url = "/member/dashboard"
    elif "staff" in user_roles:
        # fallback for staff or other roles
        redirect_url = "/staff/dashboard"
    else:
        redirect_url = "/auth/login"

    return RedirectResponse(url=redirect_url, status_code=303)

async def get_or_create_role(session: AsyncSession, role_name: str) -> Role:
    result = await session.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=role_name)
        session.add(role)
        await session.commit()
        await session.refresh(role)
    return role

# -----------------------------
# REGISTER (UI)
# -----------------------------
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("/admin/auth/register.html", {"request": request})


@router.post("/register")
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return templates.TemplateResponse(
            "/admin/auth/register.html",
            {"request": request, "error": "Email already registered"},
            status_code=400,
        )

    new_user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        status=MemberStatus.active,
        password_hash=get_password_hash(password),
        role="member",   # 👈 default role set here
        created_at=datetime.utcnow(),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Get default "member" role
    member_role = await get_or_create_role(session, "member")

    # Create user-role link
    user_role = UserRole(user_id=new_user.id, role_id=member_role.id)
    session.add(user_role)
    await session.commit()

    # ✅ auto-login after register
    access_token = create_access_token({"sub": str(new_user.id)})
    request.session["user_id"] = str(new_user.id)
    request.session["token"] = access_token

    response = RedirectResponse(url="/members/profile/edit", status_code=303)
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=False,   # set True in production with HTTPS
        samesite="lax"
    )
    return response

# -----------------------------
# LOGOUT (UI)
# -----------------------------
@router.get("/logout")
async def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=303)
