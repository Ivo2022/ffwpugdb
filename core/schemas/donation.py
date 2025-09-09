# core/schemas/donation.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
import uuid
from datetime import date
from core.models.donation import DonationType

class DonationCreate(BaseModel):
    member_id: str
    amount: float
    date: Optional[date]
    donation_date: date
    donation_type: Optional[DonationType] = DonationType.sunday_donation
    remarks: Optional[str] = None

class DonationUpdate(BaseModel):
    member_id: str
    amount: float
    donation_date: date
    donation_type: Optional[DonationType] = DonationType.sunday_donation
    remarks: Optional[date] 

class DonationRead(BaseModel):
    id: uuid.UUID
    member_id: str
    amount: float
    donation_date: date
    donation_type: Optional[DonationType] = DonationType.sunday_donation
    remarks: Optional[str] = None

    class Config:
        # orm_mode = True
        from_attributes = True  # pydantic v2
