"""Обзор прогресса по всем заданиям для капитана/менеджера."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import TaskRepo
from app.filters import is_staff
from app.utils.time import fmt_local, utcnow

router = Router(name="tasks_overview")
router.message.filter(is_staff)


@router.message(Command("tasks"))
async def overview(message: Message, session: AsyncSession):
    tasks = await TaskRepo(session).all_active()
    if not tasks:
        await message.answer("Все задания выполнены 🎉")
        return
    now = utcnow()
    lines = []
    for t in tasks:
        overdue = " 🔥" if t.deadline and t.deadline < now else ""
        lines.append(
            f"#{t.id} {t.assignee.mention()} — «{t.title}» "
            f"{len(t.items) - t.left}/{len(t.items)}, до {fmt_local(t.deadline)}{overdue}"
        )
        lines += [f"    💬 {i.text}: {i.comment}" for i in t.items if i.comment and not i.done]
    await message.answer("📋 <b>Активные задания</b>\n" + "\n".join(lines))
