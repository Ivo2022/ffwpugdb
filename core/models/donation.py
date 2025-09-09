# app/models/donation.py
from sqlmodel import SQLModel, Field, Relationship, Column , String
from datetime import date
from uuid import uuid4, UUID
from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid
from core.models.attendance import Attendance
from sqlalchemy import Date  # ✅ import Date from SQLAlchemy

class DonationType(str, Enum):
    tithe = "tithe"
    sunday_donation = "sunday donation"
    other_offering = "other offering"
    pledge = "pledge"

class Donation(SQLModel, table=True):
    __tablename__ = "donations"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    member_id: UUID = Field(foreign_key="members.id", nullable=True, index=True)
    amount: float = Field(nullable=False)
    donation_type: DonationType = Field(sa_column=Column(String, nullable=False, server_default=DonationType.sunday_donation.value), default=DonationType.sunday_donation.value)
    donation_date: date = Field(sa_column=Column("date", Date))
    remarks: str | None = Field(default=None)

    # Forward reference to Member
    member: Optional["Members"] = Relationship(back_populates="donations")