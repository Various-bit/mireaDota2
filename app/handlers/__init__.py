from aiogram import Router

from app.handlers import events, schedule, start, tasks_create, tasks_my, tasks_overview, team


def get_routers() -> list[Router]:
    # start первым: /cancel и /start должны работать из любого состояния FSM
    return [
        start.router,
        schedule.router,
        events.router,
        team.router,
        tasks_create.router,
        tasks_overview.router,
        tasks_my.router,
    ]
