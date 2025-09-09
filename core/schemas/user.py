from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    status: str
    last_login_at: datetime | None
    created_at: datetime
    role_names: list[str] = Field(default_factory=list)  # ✅ pydantic v2 syntax

class UserLogin(BaseModel):
    username: str
    password: str
