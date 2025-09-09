# core/crud/attendance.py
"""
from sqlmodel import select
from core.models.attendance import Attendance
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

async def get_attendance_by_member(db: AsyncSession, member_id):
    stmt = select(Attendance).where(Attendance.member_id == member_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_attendance(session: AsyncSession, session_id, member_ids, attendance_date, status, remarks):
    records = []
    for member_id in member_ids:       
        attendance = Attendance(
            session_id=session_id,
            member_id=member_id,
            status=status,
            remarks=remarks,
            attendance_date=attendance_date
        )
        session.add(attendance)
        records.append(attendance)

    await session.commit()
    await session.refresh(attendance)
    return records
"""

from core.crud.base import CRUDBase
from core.models.attendance import Attendance

class CRUDAttendance(CRUDBase):
    model = Attendance

attendance_crud = CRUDAttendance(Attendance)

