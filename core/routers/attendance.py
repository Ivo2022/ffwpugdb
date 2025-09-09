# core/routers/attendance.py
from fastapi import APIRouter, Depends
from core.crud.attendance import create_attendance, get_attendance_by_member
from core.schemas.attendance import AttendanceCreate, AttendanceRead
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from core.models.attendance import Attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# Dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/", response_model=AttendanceRead)
async def add_attendance(attendance: AttendanceCreate, db: AsyncSession = Depends(get_session)):
    att_obj = Attendance(**attendance.dict())
    return await create_attendance(db, att_obj)

@router.get("/{member_id}", response_model=list[AttendanceRead])
async def list_attendance(member_id: str, db: AsyncSession = Depends(get_session)):
    return await get_attendance_by_member(db, member_id)
