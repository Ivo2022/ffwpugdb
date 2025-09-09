from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from core.auth.jwt_handler import create_access_token
from core.auth.password_utils import verify_password
from app.database import async_session
from core.models.user import User
from sqlmodel import select

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/login")
async def api_login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    result = await session.execute(User.__table__.select().where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/token")
async def login_api(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    query = select(User).where(User.email == form_data.username)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create JWT for API clients
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
