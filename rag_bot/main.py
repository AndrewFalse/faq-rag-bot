import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from rag_bot.bot.handlers import router
from rag_bot.config import settings
from rag_bot.db import init_db
from rag_bot.sync.indexer import start_scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    init_db()
    start_scheduler()

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
