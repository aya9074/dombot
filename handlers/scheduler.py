from apscheduler.schedulers.asyncio import AsyncIOScheduler


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    return scheduler
