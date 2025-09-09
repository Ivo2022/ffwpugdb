# app/init_db.py  (or just in main.py on startup)
from sqlmodel import SQLModel
from app.database import engine
from core.models.chapter import Chapters
from core.models.member import Members

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
