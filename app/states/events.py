from aiogram.fsm.state import State, StatesGroup


class NewEvent(StatesGroup):
    kind = State()
    when = State()
    title = State()
