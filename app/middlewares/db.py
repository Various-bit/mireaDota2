from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import settings
from app.db.models import Role
from app.db.repositories import UserRepo
from app.db.session import sessionmaker


class DbUserMiddleware(BaseMiddleware):
    """Открывает сессию на апдейт, находит/создаёт пользователя. Кладёт session и user в data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        async with sessionmaker() as session:
            data["session"] = session
            if tg_user and not tg_user.is_bot:
                repo = UserRepo(session)
                user = await repo.get_by_tg_id(tg_user.id)
                if user is None:
                    role = Role.captain if tg_user.id in settings.captain_ids else Role.member
                    user = await repo.create(tg_user.id, tg_user.username, tg_user.full_name, role)
                else:
                    user.username = tg_user.username
                    user.full_name = tg_user.full_name
                    # капитаны из .env всегда капитаны
                    if tg_user.id in settings.captain_ids:
                        user.role = Role.captain
                data["user"] = user
            result = await handler(event, data)
            await session.commit()
            return result
