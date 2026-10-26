from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Task, User
from app.utils.time import fmt_local


class AssigneeCb(CallbackData, prefix="tassignee"):
    user_id: int


class OpenTaskCb(CallbackData, prefix="topen"):
    task_id: int


class ToggleItemCb(CallbackData, prefix="ttoggle"):
    item_id: int


class WhyItemCb(CallbackData, prefix="twhy"):
    item_id: int


def assignees_kb(users: list[User]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=u.full_name, callback_data=AssigneeCb(user_id=u.id).pack())]
            for u in users
        ]
    )


def task_list_kb(tasks: list[Task]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{t.title} · до {fmt_local(t.deadline)}",
                    callback_data=OpenTaskCb(task_id=t.id).pack(),
                )
            ]
            for t in tasks
        ]
    )


def task_view(task: Task) -> tuple[str, InlineKeyboardMarkup]:
    lines = [f"<b>{task.title}</b>", f"Дедлайн: {fmt_local(task.deadline)}", ""]
    rows = []
    for i in task.items:
        mark = "✅" if i.done else "⬜"
        lines.append(f"{mark} {i.text}" + (f"\n    💬 {i.comment}" if i.comment else ""))
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {i.text[:28]}", callback_data=ToggleItemCb(item_id=i.id).pack()
                ),
                InlineKeyboardButton(text="💬 Почему нет", callback_data=WhyItemCb(item_id=i.id).pack()),
            ]
        )
    rows.append([InlineKeyboardButton(text="← К списку", callback_data="tlist")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)
