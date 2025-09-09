# models/member.py
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
import uuid

# models/event_session.py
class EventSession(SQLModel, table=True):
    __tablename__ = "event_sessions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    event_id: uuid.UUID = Field(foreign_key="events.id")
    title: str

    # event: Event = Relationship(back_populates="sessions")
    event: "Event" = Relationship(back_populates="sessions")
    attendances: List["Attendance"] = Relationship(back_populates="session")  # ✅ matches Attendance.session


