from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.services.digest import send_weekly_digest
from app.services.notifier import Notifier
from app.services.reminders import send_event_reminders, send_task_reminders


def setup_scheduler(sm: async_sessionmaker, notifier: Notifier) -> AsyncIOScheduler:
    sch = AsyncIOScheduler(timezone=settings.tz)
    args = [sm, notifier]
    sch.add_job(send_event_reminders, "interval", minutes=1, args=args, max_instances=1)
    sch.add_job(send_task_reminders, "interval", minutes=1, args=args, max_instances=1)
    # начало / середина / конец недели
    sch.add_job(send_weekly_digest, "cron", day_of_week="mon", hour=10, args=[*args, "🗓 Начало недели"])
    sch.add_job(send_weekly_digest, "cron", day_of_week="wed", hour=12, args=[*args, "📍 Середина недели"])
    sch.add_job(send_weekly_digest, "cron", day_of_week="sun", hour=18, args=[*args, "🏁 Конец недели"])
    return sch
