from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories import EventRepo, UserRepo
from app.filters import is_staff
from app.keyboards.events import EventKindCb, event_kind_kb
from app.services.notifier import Notifier
from app.states.events import NewEvent
from app.utils.time import FMT_HINT, fmt_local, parse_local, utcnow

router = Router(name="events")
router.message.filter(is_staff)
router.callback_query.filter(is_staff)

TEXT = F.text & ~F.text.startswith("/")


@router.message(Command("newevent"))
async def newevent(message: Message, state: FSMContext):
    await state.set_state(NewEvent.kind)
    await message.answer("Что назначаем?", reply_markup=event_kind_kb())


@router.callback_query(NewEvent.kind, EventKindCb.filter())
async def pick_kind(cb: CallbackQuery, callback_data: EventKindCb, state: FSMContext):
    await state.update_data(kind=callback_data.kind.value)
    await state.set_state(NewEvent.when)
    await cb.message.answer(
        f"Когда? Формат: <code>{FMT_HINT}</code>, например <code>{fmt_local(utcnow())}</code>"
    )
    await cb.answer()


@router.message(NewEvent.when, TEXT)
async def pick_when(message: Message, state: FSMContext):
    try:
        starts_at = parse_local(message.text)
    except ValueError:
        await message.answer(f"Не понял дату. Формат: {FMT_HINT}")
        return
    if starts_at <= utcnow():
        await message.answer("Это время уже прошло.")
        return
    await state.update_data(starts_at=starts_at.isoformat())
    await state.set_state(NewEvent.title)
    await message.answer("Название / соперник / комментарий:")


@router.message(NewEvent.title, TEXT)
async def pick_title(
    message: Message, state: FSMContext, session: AsyncSession, user: User, notifier: Notifier
):
    data = await state.get_data()
    await state.clear()
    from app.db.models import EventKind

    event = await EventRepo(session).add(
        kind=EventKind(data["kind"]),
        title=message.text.strip()[:200],
        starts_at=datetime.fromisoformat(data["starts_at"]),
        created_by=user.id,
    )
    await notifier.broadcast(
        await UserRepo(session).list_all(),
        f"📌 Новое событие #{event.id}: <b>{event.kind.label}</b>\n"
        f"🕒 {fmt_local(event.starts_at)}\n{event.title}",
    )
    await message.answer(f"Готово, событие #{event.id} добавлено в расписание.")


@router.message(Command("cancelevent"))
async def cancelevent(message: Message, session: AsyncSession, notifier: Notifier):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Формат: /cancelevent <id>")
        return
    event = await EventRepo(session).get(int(parts[1]))
    if event is None or event.cancelled:
        await message.answer("Событие не найдено.")
        return
    event.cancelled = True
    await notifier.broadcast(
        await UserRepo(session).list_all(),
        f"❌ Отменено: {event.kind.label} «{event.title}» ({fmt_local(event.starts_at)})",
    )
    await message.answer("Отменено.")
