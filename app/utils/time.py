"""В БД все времена — naive UTC. Пользователь вводит/видит время в settings.tz."""
from datetime import datetime, timezone

from app.config import settings

FMT = "%d.%m.%Y %H:%M"
FMT_HINT = "ДД.ММ.ГГГГ ЧЧ:ММ"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_local(text: str) -> datetime:
    """'25.10.2026 19:30' (в TIMEZONE) -> naive UTC. ValueError при ошибке."""
    local = datetime.strptime(text.strip(), FMT).replace(tzinfo=settings.tz)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def fmt_local(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.replace(tzinfo=timezone.utc).astimezone(settings.tz).strftime(FMT)
