"""Напоминания по БД: раз в минуту выбираем, что «пора». Дедуп через *_reminders —
переживает рестарт, не требует перепланирования при создании/отмене событий."""
from datetime import timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.db.repositories import EventRepo, TaskRepo, UserRepo
from app.services.notifier import Notifier
from app.utils.time import fmt_local, utcnow

OFFSET_LABEL = {1440: "24 часа", 180: "3 часа", 60: "1 час", 30: "30 минут"}


def label(minutes: int) -> str:
    return OFFSET_LABEL.get(minutes, f"{minutes} мин")


def due_offsets(left: timedelta, offsets: tuple[int, ...], sent: set[int]) -> list[int]:
    """Пороги, которые уже наступили и по которым ещё не слали."""
    return [o for o in offsets if left <= timedelta(minutes=o) and o not in sent]


async def send_event_reminders(sm: async_sessionmaker, notifier: Notifier) -> None:
    now = utcnow()
    async with sm() as s:
        events = await EventRepo(s).starting_within(now, max(settings.event_offsets))
        if not events:
            return
        users = await UserRepo(s).list_all()
        for ev in events:
            due = due_offsets(
                ev.starts_at - now, settings.event_offsets, {r.offset_minutes for r in ev.reminders}
            )
            if not due:
                continue
            # событие создали поздно — шлём только самое близкое напоминание, остальные гасим
            EventRepo(s).mark_reminded(ev.id, due)
            await notifier.broadcast(
                users,
                f"⏰ Через {label(min(due))}: <b>{ev.kind.label}</b>\n"
                f"🕒 {fmt_local(ev.starts_at)}\n{ev.title}",
            )
        await s.commit()


async def send_task_reminders(sm: async_sessionmaker, notifier: Notifier) -> None:
    now = utcnow()
    async with sm() as s:
        repo = TaskRepo(s)
        for task in await repo.with_deadline_before(now + timedelta(minutes=max(settings.task_offsets))):
            sent = {r.offset_minutes for r in task.reminders}
            left = task.deadline - now  # type: ignore[operator]

            if left <= timedelta(0):
                if 0 not in sent:  # просрочка: один раз, исполнителю и выдавшему
                    repo.mark_reminded(task.id, [0])
                    text = f"🔥 Просрочено: «{task.title}» (дедлайн {fmt_local(task.deadline)}), осталось пунктов: {task.left}"
                    await notifier.send(task.assignee.tg_id, text)
                    await notifier.send(task.assigner.tg_id, f"{task.assignee.mention()}: {text}")
                continue

            due = due_offsets(left, settings.task_offsets, sent)
            if due:
                repo.mark_reminded(task.id, due)
                await notifier.send(
                    task.assignee.tg_id,
                    f"⏳ Через {label(min(due))} дедлайн: «{task.title}», "
                    f"осталось пунктов: {task.left}\n/mytasks",
                )
        await s.commit()
