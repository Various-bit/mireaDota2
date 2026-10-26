"""Выдача заданий — только капитан/менеджер."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories import TaskRepo, UserRepo
from app.filters import is_staff
from app.keyboards.tasks import AssigneeCb, assignees_kb
from app.services.notifier import Notifier
from app.states.tasks import NewTask
from app.utils.time import FMT_HINT, fmt_local, parse_local

router = Router(name="tasks_create")
router.message.filter(is_staff)
router.callback_query.filter(is_staff)

TEXT = F.text & ~F.text.startswith("/")


@router.message(Command("newtask"))
async def newtask(message: Message, state: FSMContext, session: AsyncSession):
    await state.set_state(NewTask.assignee)
    await message.answer("Кому задание?", reply_markup=assignees_kb(await UserRepo(session).list_all()))


@router.callback_query(NewTask.assignee, AssigneeCb.filter())
async def pick_assignee(cb: CallbackQuery, callback_data: AssigneeCb, state: FSMContext):
    await state.update_data(assignee_id=callback_data.user_id, items=[])
    await state.set_state(NewTask.title)
    await cb.message.answer("Название задания:")
    await cb.answer()


@router.message(NewTask.title, TEXT)
async def pick_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip()[:200])
    await state.set_state(NewTask.items)
    await message.answer("Присылай пункты по одному сообщению. Когда хватит — /done")


@router.message(NewTask.items, Command("done"))
async def items_done(message: Message, state: FSMContext):
    if not (await state.get_data())["items"]:
        await message.answer("Нужен хотя бы один пункт.")
        return
    await state.set_state(NewTask.deadline)
    await message.answer(f"Дедлайн <code>{FMT_HINT}</code> или «-» без дедлайна:")


@router.message(NewTask.items, TEXT)
async def add_item(message: Message, state: FSMContext):
    items = (await state.get_data())["items"]
    items.append(message.text.strip()[:500])
    await state.update_data(items=items)
    await message.answer(f"Пункт {len(items)} добавлен. Ещё или /done")


@router.message(NewTask.deadline, TEXT)
async def pick_deadline(
    message: Message, state: FSMContext, session: AsyncSession, user: User, notifier: Notifier
):
    text = message.text.strip()
    deadline = None
    if text != "-":
        try:
            deadline = parse_local(text)
        except ValueError:
            await message.answer(f"Не понял дату. Формат: {FMT_HINT} или «-»")
            return
    data = await state.get_data()
    await state.clear()

    task = await TaskRepo(session).add(
        title=data["title"],
        assignee_id=data["assignee_id"],
        assigner_id=user.id,
        deadline=deadline,
        items=data["items"],
    )
    await notifier.send(
        task.assignee.tg_id,
        f"📝 Новое задание от {user.mention()}: <b>{task.title}</b>\n"
        f"Пунктов: {len(task.items)}, дедлайн: {fmt_local(deadline)}\nОткрыть: /mytasks",
    )
    await message.answer(f"Задание #{task.id} выдано {task.assignee.mention()}.")
