from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import EventRepo
from app.utils.time import fmt_local, utcnow

router = Router(name="schedule")


@router.message(Command("schedule"))
async def schedule(message: Message, session: AsyncSession):
    events = await EventRepo(session).upcoming(utcnow())
    if not events:
        await message.answer("Ближайших событий нет.")
        return
    lines = [
        f"#{e.id} · <b>{e.kind.label}</b> · {fmt_local(e.starts_at)} · {e.title}" for e in events
    ]
    await message.answer("📅 <b>Расписание</b>\n" + "\n".join(lines))
