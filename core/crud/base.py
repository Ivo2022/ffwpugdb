from sqlmodel import SQLModel, select
from sqlalchemy import func, or_
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Type, TypeVar, Generic, Optional, Dict, Any

ModelType = TypeVar("ModelType", bound=SQLModel)

class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    # ------------------------
    # Create
    # ------------------------
    async def create(self, session: AsyncSession, obj_in: dict | ModelType) -> ModelType:
        obj = obj_in if isinstance(obj_in, self.model) else self.model(**obj_in)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    # ------------------------
    # Get by ID
    # ------------------------
    async def get(self, session: AsyncSession, id: Any, with_relationships: bool = False) -> Optional[ModelType]:
        if with_relationships:
            stmt = (
                select(self.model)
                .where(self.model.id == id)
                .options(selectinload("*"))  # loads all relationships
            )
            result = await session.execute(stmt)
            return result.scalars().first()
        return await session.get(self.model, id)

    # ------------------------
    # Update
    # ------------------------
    async def update(self, session: AsyncSession, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    # ------------------------
    # Delete
    # ------------------------
    async def delete(self, session: AsyncSession, db_obj: ModelType):
        await session.delete(db_obj)
        await session.commit()

    # ------------------------
    # Count filtered rows (generic)
    # filters: dict of field -> value
    # ------------------------   
    async def count_filtered(self, session: AsyncSession, q: Optional[str] = None, filters: Optional[Dict[str, Any]] = None, search_fields: Optional[list] = None,) -> int:
        from sqlalchemy import or_, func

        stmt = select(func.count()).select_from(self.model)

        # Apply search filter
        if q and search_fields:
            like = f"%{q}%"
            conditions = [
                func.lower(getattr(self.model, f)).like(func.lower(like))
                for f in search_fields
                if hasattr(self.model, f)
            ]
            if conditions:
                stmt = stmt.where(or_(*conditions))

        # Apply other filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)

        result = await session.execute(stmt)
        total = result.scalar_one()  # returns int
        return total

    # ------------------------
    # Select statement for list pages (generic)
    # ------------------------
    def select_stmt(self, q: Optional[str] = None, filters: Optional[Dict[str, Any]] = None, search_fields: Optional[list] = None, page: int = 1, page_size: int = 10, order_by: Optional[str] = None, descending: bool = True,):
        from sqlalchemy import or_, func

        stmt = select(self.model)

        # Apply search filter
        if q and search_fields:
            like = f"%{q}%"
            conditions = [
                func.lower(getattr(self.model, f)).like(func.lower(like))
                for f in search_fields
                if hasattr(self.model, f)
            ]
            if conditions:
                stmt = stmt.where(or_(*conditions))

        # Apply other filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)

        # Apply ordering if valid
        if order_by and hasattr(self.model, order_by):
            field_attr = getattr(self.model, order_by)
            stmt = stmt.order_by(field_attr.desc() if descending else field_attr.asc())
        else:
            # Fallback: use the first column in the model (optional)
            # first_column = next(iter(self.model.__fields__.values()), None)
            first_column = next(iter(self.model.__table__.columns), None)
            if first_column is not None:
                field_attr = getattr(self.model, first_column.name)
                stmt = stmt.order_by(field_attr.desc() if descending else field_attr.asc())

        # Pagination
        stmt = stmt.limit(page_size).offset((page - 1) * page_size)

        return stmt
