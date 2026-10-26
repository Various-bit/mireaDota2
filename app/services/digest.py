"""Недельные уведомления: начало / середина / конец недели."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.repositories import EventRepo, TaskRepo
from app.services.notifier import Notifier
from app.utils.time import fmt_local, utcnow


async def send_weekly_digest(sm: async_sessionmaker, notifier: Notifier, title: str) -> None:
    now = utcnow()
    async with sm() as s:
        tasks = await TaskRepo(s).all_active()
        events = await EventRepo(s).upcoming(now, limit=5)

        by_user: dict[int, list] = {}
        for t in tasks:
            by_user.setdefault(t.assignee_id, []).append(t)

        events_block = "\n".join(
            f"• {e.kind.label} {fmt_local(e.starts_at)} — {e.title}" for e in events
        )
        for user_tasks in by_user.values():
            lines = []
            for t in user_tasks:
                overdue = " 🔥 просрочено" if t.deadline and t.deadline < now else ""
                lines.append(f"• {t.title} — осталось {t.left}, до {fmt_local(t.deadline)}{overdue}")
            text = f"{title}\n<b>Невыполненные задания:</b>\n" + "\n".join(lines)
            if events_block:
                text += f"\n\n<b>Ближайшие события:</b>\n{events_block}"
            await notifier.send(user_tasks[0].assignee.tg_id, text + "\n\n/mytasks")
