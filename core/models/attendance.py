# app/models/attendance.py
from sqlmodel import SQLModel, Field, Relationship, Column, String
from datetime import date as dt_date
from uuid import uuid4, UUID
from enum import Enum
from typing import List, Optional
from core.models.event import Event
from core.models.event_session import EventSession


class AttendanceStatus(str, Enum):
    present = "Present"
    absent = "Absent"
    online = "Online"
    excused = "Excused"

class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    member_id: UUID = Field(foreign_key="members.id", nullable=False)
    session_id: UUID = Field(foreign_key="event_sessions.id", nullable=False)
    attendance_date: dt_date = Field(nullable=False, index=True)
    status: str | None = Field(default="present") 
    remarks: str | None = Field(default=None)

    # member: Member = Relationship(back_populates="attendances")
    # member: "Members" = Relationship(back_populates="attendances")
    member: Optional["Members"] = Relationship(back_populates="attendances")
    session: Optional["EventSession"] = Relationship(back_populates="attendances")