import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    captain_ids: frozenset[int]
    tz: ZoneInfo
    database_url: str
    # за сколько минут до КВ/официалки напоминать всем
    event_offsets: tuple[int, ...] = (24 * 60, 3 * 60, 60, 30)
    # за сколько минут до дедлайна задания напоминать исполнителю
    task_offsets: tuple[int, ...] = (24 * 60, 3 * 60)


def load_settings() -> Settings:
    return Settings(
        bot_token=os.environ["BOT_TOKEN"],
        captain_ids=frozenset(
            int(x) for x in os.getenv("CAPTAIN_IDS", "").split(",") if x.strip()
        ),
        tz=ZoneInfo(os.getenv("TIMEZONE", "Europe/Moscow")),
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db"),
    )


settings = load_settings()
