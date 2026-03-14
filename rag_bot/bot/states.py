from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    choosing_topic = State()
    asking_question = State()
