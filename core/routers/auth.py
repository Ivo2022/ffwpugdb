from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from core.models.user import User
from core.schemas.user import UserCreate, UserRead
from core.auth.jwt_handler import create_access_token, decode_access_token
from core.auth.password_utils import verify_password, get_password_hash
from sqlmodel import select

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

# --- Render login page ---
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

# --- Handle login form ---
@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_session)
):
    query = select(User).where(User.email == email)
    result = await db.exec(query)
    user = result.first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid email or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # create JWT token
    access_token = create_access_token({"sub": str(user.id)})

    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

# --- Logout ---
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

# --- Register page ---
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

# --- Handle registration form ---
@router.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    query = select(User).where(User.email == email)
    existing = (await db.exec(query)).first()
    if existing:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Email already registered"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    new_user = User(
        name=name,
        email=email,
        password_hash=get_password_hash(password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
