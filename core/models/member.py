from sqlmodel import SQLModel, Field, Column, String, Relationship
from typing import Optional, List
from datetime import date, datetime
import uuid
from enum import Enum
from .donation import Donation
from core.models.attendance import Attendance

class MemberStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    alumni = "alumni"
    guest = "guest"

class Gender(str, Enum):
    select = "select gender"
    male = "male"
    female = "female"

class Members(SQLModel, table=True):
    __tablename__ = "members"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    member_code: str = Field(unique=True, nullable=False, max_length=50)

    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    other_names: Optional[str] = Field(default=None, max_length=100)

    gender: Gender = Field(sa_column=Column(String, nullable=False, server_default=Gender.select.value), default=Gender.select.value)
    dob: Optional[date] = None
    national_id: Optional[str] = Field(default=None, max_length=50)

    phone: Optional[str] = Field(default=None, max_length=30, unique=True)
    email: Optional[str] = Field(default=None, max_length=100, unique=True)

    address: Optional[str] = None
    chapter_id: Optional[uuid.UUID] = Field(default=None, foreign_key="chapters.id")

    status: MemberStatus = Field(sa_column=Column(String, nullable=False, server_default=MemberStatus.active.value), default=MemberStatus.active.value)
    join_date: date = Field(default_factory=date.today)

    photo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    # attendance_records: list[Attendance] = Relationship(back_populates="member")
    attendances: List["Attendance"] = Relationship(back_populates="member")
    # Backref for donations
    donations: List["Donation"] = Relationship(back_populates="member")