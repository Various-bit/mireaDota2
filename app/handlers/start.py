from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db.models import User

router = Router(name="start")

HELP = (
    "<b>Команды</b>\n"
    "/schedule — расписание КВ и официалок\n"
    "/mytasks — мои задания\n"
    "/cancel — отменить текущее действие\n"
    "\n<b>Капитан / менеджер</b>\n"
    "/newevent — назначить КВ/официалку\n"
    "/cancelevent &lt;id&gt; — отменить событие\n"
    "/newtask — выдать задание\n"
    "/tasks — прогресс по всем заданиям\n"
    "/team — список команды\n"
    "\n<b>Капитан</b>\n"
    "/setrole &lt;tg_id&gt; &lt;member|manager|captain&gt;"
)


@router.message(CommandStart())
async def start(message: Message, user: User, state: FSMContext):
    await state.clear()
    await message.answer(f"Привет, {user.full_name}! Твоя роль: <b>{user.role.value}</b>.\n\n{HELP}")


@router.message(Command("help"))
async def help_(message: Message):
    await message.answer(HELP)


@router.message(Command("cancel"), StateFilter("*"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.")
