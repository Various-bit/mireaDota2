from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Role, User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.tg_id == tg_id))

    async def create(self, tg_id: int, username: str | None, full_name: str, role: Role) -> User:
        user = User(tg_id=tg_id, username=username, full_name=full_name, role=role)
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_all(self) -> list[User]:
        return list((await self.session.scalars(select(User).order_by(User.full_name))).all())
