import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventKind(str, enum.Enum):
    scrim = "scrim"  # КВ
    practice = "practice"

    @property
    def label(self) -> str:
        return "КВ" if self is EventKind.scrim else "Официалка"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[EventKind] = mapped_column(Enum(EventKind))
    title: Mapped[str] = mapped_column(String(200))
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    cancelled: Mapped[bool] = mapped_column(default=False)

    reminders: Mapped[list["EventReminder"]] = relationship(
        cascade="all, delete-orphan"
    )


class EventReminder(Base):
    """Факт отправки напоминания (защита от дублей, переживает рестарт)."""

    __tablename__ = "event_reminders"
    __table_args__ = (UniqueConstraint("event_id", "offset_minutes"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    offset_minutes: Mapped[int]
