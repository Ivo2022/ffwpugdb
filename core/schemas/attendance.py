# core/schemas/attendance.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime, date
from core.models.attendance import AttendanceStatus


class AttendanceCreate(BaseModel):
    session_id: UUID
    member_ids: List[UUID]   # multiple members selected
    status: Optional[AttendanceStatus] = AttendanceStatus.present
    remarks: str | None = None
    attendance_date: date

class AttendanceRead(BaseModel):
    id: UUID
    member_id: UUID
    session_id: UUID
    attendance_date: date
    status: Optional[AttendanceStatus] = AttendanceStatus.present
    remarks: str | None = None

class AttendanceUpdate(BaseModel):
    attendance_date: date
    status: Optional[AttendanceStatus] = AttendanceStatus.present

    class Config:
        # orm_mode = True
        from_attributes = True  # pydantic v2
