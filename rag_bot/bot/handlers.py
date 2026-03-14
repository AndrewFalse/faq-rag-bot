import asyncio

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from rag_bot.bot.keyboards import change_topic_keyboard, topic_keyboard
from rag_bot.bot.states import UserState
from rag_bot.rag.pipeline import get_answer

router = Router()

_TOPIC_LABELS: dict[str, str] = {
    "RPD": "📄 РПД",
    "GIA": "📋 ГИА",
    "ALL": "🗂 Все документы",
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привет! Я помогу найти ответы в документах.\nВыберите тему:",
        reply_markup=topic_keyboard(),
    )
    await state.set_state(UserState.choosing_topic)


@router.callback_query(F.data.startswith("topic_"))
async def topic_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    topic = callback.data.removeprefix("topic_")
    await state.update_data(topic=topic)
    label = _TOPIC_LABELS.get(topic, topic)
    await callback.message.edit_text(f"Выбрана тема: {label}. Задайте вопрос:")
    await state.set_state(UserState.asking_question)
    await callback.answer()


@router.callback_query(F.data == "change_topic")
async def change_topic(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Выберите тему:", reply_markup=topic_keyboard()
    )
    await state.set_state(UserState.choosing_topic)
    await callback.answer()


@router.message(UserState.asking_question, F.text)
async def handle_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    topic = data.get("topic", "ALL")

    waiting = await message.answer("Ищу ответ...")

    result = await asyncio.to_thread(get_answer, message.text, topic)

    text = result["answer"]
    if result["sources"]:
        sources = ", ".join(result["sources"])
        text += f"\n\n📎 Источники: {sources}"

    await waiting.delete()
    await message.answer(text, reply_markup=change_topic_keyboard())
