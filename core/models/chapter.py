from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

class Chapters(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(max_length=150, nullable=False)
    
    # Self-referencing foreign key to parent chapter
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="chapter.id")
    
    type: Optional[str] = Field(default=None, max_length=20)  # national, region, district, center
    address: Optional[str] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None, max_length=30)
    active: bool = Field(default=True)
