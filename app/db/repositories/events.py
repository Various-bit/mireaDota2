from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Event, EventKind, EventReminder


class EventRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, kind: EventKind, title: str, starts_at: datetime, created_by: int) -> Event:
        event = Event(kind=kind, title=title, starts_at=starts_at, created_by=created_by)
        self.session.add(event)
        await self.session.flush()
        return event

    async def get(self, event_id: int) -> Event | None:
        return await self.session.get(Event, event_id)

    async def upcoming(self, now: datetime, limit: int = 20) -> list[Event]:
        q = (
            select(Event)
            .where(Event.starts_at >= now, Event.cancelled.is_(False))
            .order_by(Event.starts_at)
            .limit(limit)
        )
        return list((await self.session.scalars(q)).all())

    async def starting_within(self, now: datetime, minutes: int) -> list[Event]:
        """Будущие неотменённые события в окне [now, now+minutes] вместе с отправленными напоминаниями."""
        q = (
            select(Event)
            .where(
                Event.starts_at > now,
                Event.starts_at <= now + timedelta(minutes=minutes),
                Event.cancelled.is_(False),
            )
            .options(selectinload(Event.reminders))
        )
        return list((await self.session.scalars(q)).all())

    def mark_reminded(self, event_id: int, offsets: list[int]) -> None:
        for o in offsets:
            self.session.add(EventReminder(event_id=event_id, offset_minutes=o))
