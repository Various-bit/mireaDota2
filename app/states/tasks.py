from aiogram.fsm.state import State, StatesGroup


class NewTask(StatesGroup):
    assignee = State()
    title = State()
    items = State()
    deadline = State()


class Reason(StatesGroup):
    comment = State()
