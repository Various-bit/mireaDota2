from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.db.models import Role, User


class RoleFilter(BaseFilter):
    def __init__(self, *roles: Role):
        self.roles = set(roles)

    async def __call__(self, event: TelegramObject, user: User | None = None) -> bool:
        return user is not None and user.role in self.roles


is_staff = RoleFilter(Role.captain, Role.manager)  # капитан и менеджер
is_captain = RoleFilter(Role.captain)
