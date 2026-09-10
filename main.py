import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import start, room, tasks, reports
from handlers.scheduler import setup_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # 1. Инициализация БД
    init_db()
    logger.info("БД инициализирована")

    # 2. Бот и диспетчер
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(room.router)
    dp.include_router(tasks.router)
    dp.include_router(reports.router)

    # 4. Планировщик напоминаний
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Планировщик запущен")

    # 5. Запуск polling
    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        scheduler.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
