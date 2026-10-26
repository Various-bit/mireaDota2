"""Задания участника: чек-лист, отметка выполнения, комментарий «почему не сделано»."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task, User
from app.db.repositories import TaskRepo
from app.keyboards.tasks import (
    OpenTaskCb,
    ToggleItemCb,
    WhyItemCb,
    task_list_kb,
    task_view,
)
from app.services.notifier import Notifier
from app.states.tasks import Reason

router = Router(name="tasks_my")

TEXT = F.text & ~F.text.startswith("/")


async def _own_task(session: AsyncSession, user: User, task_id: int | None) -> Task | None:
    task = await TaskRepo(session).get(task_id) if task_id else None
    return task if task and task.assignee_id == user.id else None


@router.message(Command("mytasks"))
async def mytasks(message: Message, session: AsyncSession, user: User):
    tasks = await TaskRepo(session).active_for_assignee(user.id)
    if not tasks:
        await message.answer("Активных заданий нет 🎉")
        return
    await message.answer("Твои задания:", reply_markup=task_list_kb(tasks))


@router.callback_query(F.data == "tlist")
async def back_to_list(cb: CallbackQuery, session: AsyncSession, user: User):
    tasks = await TaskRepo(session).active_for_assignee(user.id)
    if tasks:
        await cb.message.edit_text("Твои задания:", reply_markup=task_list_kb(tasks))
    else:
        await cb.message.edit_text("Активных заданий нет 🎉")
    await cb.answer()


@router.callback_query(OpenTaskCb.filter())
async def open_task(cb: CallbackQuery, callback_data: OpenTaskCb, session: AsyncSession, user: User):
    task = await _own_task(session, user, callback_data.task_id)
    if task is None:
        await cb.answer("Нет доступа", show_alert=True)
        return
    text, kb = task_view(task)
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


@router.callback_query(ToggleItemCb.filter())
async def toggle(
    cb: CallbackQuery,
    callback_data: ToggleItemCb,
    session: AsyncSession,
    user: User,
    notifier: Notifier,
):
    repo = TaskRepo(session)
    item = await repo.get_item(callback_data.item_id)
    task = await _own_task(session, user, item.task_id if item else None)
    if task is None:
        await cb.answer("Нет доступа", show_alert=True)
        return
    item = next(i for i in task.items if i.id == callback_data.item_id)
    item.done = not item.done
    if item.done:
        item.comment = None
    text, kb = task_view(task)
    await cb.message.edit_text(text, reply_markup=kb)
    if item.done and task.is_done:
        await notifier.send(task.assigner.tg_id, f"✅ {user.mention()} выполнил(а) задание «{task.title}»")
    await cb.answer()


@router.callback_query(WhyItemCb.filter())
async def why(cb: CallbackQuery, callback_data: WhyItemCb, state: FSMContext):
    await state.set_state(Reason.comment)
    await state.update_data(item_id=callback_data.item_id)
    await cb.message.answer("Напиши, почему не сделано (или /cancel):")
    await cb.answer()


@router.message(Reason.comment, TEXT)
async def why_text(
    message: Message, state: FSMContext, session: AsyncSession, user: User, notifier: Notifier
):
    item_id = (await state.get_data())["item_id"]
    await state.clear()
    item = await TaskRepo(session).get_item(item_id)
    task = await _own_task(session, user, item.task_id if item else None)
    if task is None:
        await message.answer("Нет доступа")
        return
    item = next(i for i in task.items if i.id == item_id)
    item.comment = message.text.strip()[:1000]
    await notifier.send(
        task.assigner.tg_id,
        f"⚠️ {user.mention()} по заданию «{task.title}», пункт «{item.text}»:\n{item.comment}",
    )
    await message.answer("Комментарий отправлен. Вернуться к списку: /mytasks")
