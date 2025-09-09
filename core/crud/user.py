from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from core.models.user import User
from core.models.member import Members


class UserCRUD:
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str):
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user: User):
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_with_member(user_id: int, db: AsyncSession):
        statement = select(User, Members).join(Members, Members.user_id == User.id).where(User.id == user_id)
        
        # Await the execute coroutine first
        result_proxy = await db.execute(statement)
        
        # Then fetch the first row
        result = result_proxy.first()
        
        if result:
            user, member = result
            return user, member
        return None, None