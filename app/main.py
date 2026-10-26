import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.config import settings
from app.db.session import init_db, sessionmaker
from app.handlers import get_routers
from app.middlewares import DbUserMiddleware
from app.scheduler import setup_scheduler
from app.services.notifier import Notifier

COMMANDS = [
    BotCommand(command="schedule", description="Расписание КВ и официалок"),
    BotCommand(command="mytasks", description="Мои задания"),
    BotCommand(command="newevent", description="Назначить КВ/официалку (staff)"),
    BotCommand(command="newtask", description="Выдать задание (staff)"),
    BotCommand(command="tasks", description="Прогресс по заданиям (staff)"),
    BotCommand(command="cancel", description="Отменить действие"),
    BotCommand(command="help", description="Помощь"),
]


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    notifier = Notifier(bot)
    dp = Dispatcher(notifier=notifier)  # доступен в хендлерах как аргумент `notifier`
    dp.update.outer_middleware(DbUserMiddleware())
    dp.include_routers(*get_routers())

    await bot.set_my_commands(COMMANDS)
    scheduler = setup_scheduler(sessionmaker, notifier)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
