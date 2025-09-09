from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Async session
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Utility to create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
