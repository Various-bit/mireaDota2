from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import EventKind


class EventKindCb(CallbackData, prefix="evkind"):
    kind: EventKind


def event_kind_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=k.label, callback_data=EventKindCb(kind=k).pack())
                for k in EventKind
            ]
        ]
    )
