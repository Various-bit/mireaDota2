from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Role
from app.db.repositories import UserRepo
from app.filters import is_captain, is_staff

router = Router(name="team")


@router.message(Command("team"), is_staff)
async def team(message: Message, session: AsyncSession):
    users = await UserRepo(session).list_all()
    await message.answer(
        "\n".join(f"{u.mention()} · <code>{u.tg_id}</code> · {u.role.value}" for u in users)
    )


@router.message(Command("setrole"), is_captain)
async def setrole(message: Message, session: AsyncSession):
    parts = (message.text or "").split()
    try:
        tg_id, role = int(parts[1]), Role(parts[2])
    except (IndexError, ValueError):
        await message.answer("Формат: /setrole <tg_id> <member|manager|captain>")
        return
    target = await UserRepo(session).get_by_tg_id(tg_id)
    if target is None:
        await message.answer("Пользователь не найден (он должен сначала написать боту /start).")
        return
    target.role = role
    await message.answer(f"{target.mention()} → {role.value}")
