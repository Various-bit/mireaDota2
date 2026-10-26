from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Task, TaskItem, TaskReminder

_FULL = (
    selectinload(Task.items),
    selectinload(Task.reminders),
    selectinload(Task.assignee),
    selectinload(Task.assigner),
)


class TaskRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        title: str,
        assignee_id: int,
        assigner_id: int,
        deadline: datetime | None,
        items: list[str],
    ) -> Task:
        task = Task(
            title=title,
            assignee_id=assignee_id,
            assigner_id=assigner_id,
            deadline=deadline,
            items=[TaskItem(text=t) for t in items],
        )
        self.session.add(task)
        await self.session.flush()
        return await self.get(task.id)  # type: ignore[return-value]

    async def get(self, task_id: int) -> Task | None:
        return await self.session.scalar(select(Task).where(Task.id == task_id).options(*_FULL))

    async def get_item(self, item_id: int) -> TaskItem | None:
        return await self.session.get(TaskItem, item_id)

    async def active_for_assignee(self, user_id: int) -> list[Task]:
        q = select(Task).where(Task.assignee_id == user_id).options(*_FULL)
        tasks = (await self.session.scalars(q)).all()
        return sorted((t for t in tasks if not t.is_done), key=_by_deadline)

    async def all_active(self) -> list[Task]:
        tasks = (await self.session.scalars(select(Task).options(*_FULL))).all()
        return sorted((t for t in tasks if not t.is_done), key=_by_deadline)

    async def with_deadline_before(self, horizon: datetime) -> list[Task]:
        """Незавершённые задания с дедлайном до horizon (включая просроченные)."""
        q = select(Task).where(Task.deadline.is_not(None), Task.deadline <= horizon).options(*_FULL)
        return [t for t in (await self.session.scalars(q)).all() if not t.is_done]

    def mark_reminded(self, task_id: int, offsets: list[int]) -> None:
        for o in offsets:
            self.session.add(TaskReminder(task_id=task_id, offset_minutes=o))


def _by_deadline(t: Task) -> datetime:
    return t.deadline or datetime.max


__all__ = ["TaskRepo", "timedelta"]
