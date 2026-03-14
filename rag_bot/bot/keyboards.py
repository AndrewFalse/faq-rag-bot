from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def topic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 РПД", callback_data="topic_RPD"),
            InlineKeyboardButton(text="📋 ГИА", callback_data="topic_GIA"),
        ],
        [
            InlineKeyboardButton(text="🗂 Все документы", callback_data="topic_ALL"),
        ],
    ])


def change_topic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сменить тему", callback_data="change_topic")],
    ])
