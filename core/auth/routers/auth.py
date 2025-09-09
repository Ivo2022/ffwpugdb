# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import async_session
from core.auth.jwt_handler import create_access_token
from core.models.user import User
from core.schemas.user import UserLogin, UserRead
from core.auth.password_utils import verify_password
from sqlmodel import Session, select

router = APIRouter()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
"""
@router.post("/login", response_model=UserRead)
async def login(user: UserLogin, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer", "user": db_user}

"""

@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_session)):
    result = await db.exec(select(User).where(User.email == user_data.email))
    #db_user = result.scalar_one_or_none()
    db_user = result.first()

    if not db_user or not verify_password(user_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer", "user": db_user}

@router.get("/me", response_model=UserRead)
def get_current_user(token: str, db: Session = Depends(get_session)):
    from app.auth.jwt_handler import decode_access_token
    payload = decode_access_token(token)
    user = db.exec(select(User).where(User.id == payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user 