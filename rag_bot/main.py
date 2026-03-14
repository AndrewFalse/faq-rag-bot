import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from rag_bot.admin.app import app as admin_app
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

    server = uvicorn.Server(
        uvicorn.Config(admin_app, host="0.0.0.0", port=8080, log_level="info"),
    )

    await asyncio.gather(
        dp.start_polling(bot),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
