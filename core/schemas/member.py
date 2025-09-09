# app/core/schemas/member.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from core.models.member import MemberStatus, Gender
import uuid

class MemberCreate(BaseModel):
    member_code: str = Field(min_length=1, max_length=50)
    first_name: str
    last_name: str
    other_names: Optional[str] = None
    gender: Optional[Gender] = Gender.select
    dob: Optional[date] = None
    national_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    chapter_id: Optional[uuid.UUID] = None
    status: Optional[MemberStatus] = MemberStatus.active
    join_date: Optional[date] = None
    photo_url: Optional[str] = None

class MemberUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    other_names: Optional[str] = None
    gender: Optional[Gender] = Gender.select
    dob: Optional[date] 
    national_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    chapter_id: Optional[uuid.UUID] = None
    status: Optional[MemberStatus] = MemberStatus.inactive
    photo_url: Optional[str] = None

class MemberRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    member_code: str
    first_name: str
    last_name: str
    other_names: Optional[str] = None
    gender: Optional[Gender] = Gender.select
    dob: Optional[date] = None
    national_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    chapter_id: Optional[uuid.UUID] = None
    status: Optional[MemberStatus] = MemberStatus.active
    join_date: date
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        # orm_mode = True
        from_attributes = True  # pydantic v2
