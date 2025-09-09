from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import uuid

# Association table
class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"   # <-- important
    
    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True, default_factory=uuid.uuid4)
    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True, default_factory=uuid.uuid4)

class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str

    # Optional: back reference to users
    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str
    email: str = Field(nullable=False, unique=True, index=True)
    password_hash: str = Field(nullable=False)
    status: Optional[str] = "active"
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ORM relationship
    roles: List[Role] = Relationship(back_populates="users", link_model=UserRole)

    class Config:
        arbitrary_types_allowed = True  # allow dynamic attributes
