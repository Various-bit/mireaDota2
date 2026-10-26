from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.user import User


class Task(Base):
    """Персональное задание = чек-лист для одного участника."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    deadline: Mapped[datetime | None] = mapped_column(DateTime)  # UTC naive
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assignee: Mapped[User] = relationship(foreign_keys=[assignee_id])
    assigner: Mapped[User] = relationship(foreign_keys=[assigner_id])
    items: Mapped[list["TaskItem"]] = relationship(
        cascade="all, delete-orphan", order_by="TaskItem.id"
    )
    reminders: Mapped[list["TaskReminder"]] = relationship(cascade="all, delete-orphan")

    @property
    def is_done(self) -> bool:
        return bool(self.items) and all(i.done for i in self.items)

    @property
    def left(self) -> int:
        return sum(1 for i in self.items if not i.done)


class TaskItem(Base):
    __tablename__ = "task_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    text: Mapped[str] = mapped_column(String(500))
    done: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str | None] = mapped_column(String(1000))  # почему не сделано


class TaskReminder(Base):
    """Отправленные напоминания о дедлайне. offset_minutes=0 — уведомление о просрочке."""

    __tablename__ = "task_reminders"
    __table_args__ = (UniqueConstraint("task_id", "offset_minutes"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    offset_minutes: Mapped[int]
