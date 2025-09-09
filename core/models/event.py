# models/member.py
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
import uuid

# models/event.py
class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    title: str
    description: Optional[str] = None

    sessions: List["EventSession"] = Relationship(back_populates="event")
