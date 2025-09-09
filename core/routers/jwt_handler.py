"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.database import async_session
from core.models.member import Members
from typing import List
from sqlmodel import SQLModel

router = APIRouter()
"""

from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from uuid import uuid4


PWD_CTX = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-a-secure-random-value")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


# Password helpers
def hash_password(password: str) -> str:
    return PWD_CTX.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return PWD_CTX.verify(plain_password, hashed_password)

# JWT helpers
def _now():
    return datetime.utcnow()

def create_access_token(subject: str, extra: dict | None = None, expires_delta: timedelta | None = None):
    now = _now()
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": subject, "iat": now, "exp": now + expires_delta, "jti": str(uuid4())}
        if extra:
            to_encode.update(extra)
            return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(subject: str, expires_delta: timedelta | None = None):
    now = _now()
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {"sub": subject, "iat": now, "exp": now + expires_delta, "jti": str(uuid4())}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
        except JWTError:
            return None