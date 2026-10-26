import logging

from aiogram import Bot

from app.db.models import User

log = logging.getLogger(__name__)


class Notifier:
    """Единственное место, где бот пишет пользователям по инициативе системы."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send(self, tg_id: int, text: str) -> bool:
        try:
            await self.bot.send_message(tg_id, text)
            return True
        except Exception as e:  # заблокировал бота / не писал ему
            log.warning("send to %s failed: %s", tg_id, e)
            return False

    async def broadcast(self, users: list[User], text: str) -> None:
        for u in users:
            await self.send(u.tg_id, text)
