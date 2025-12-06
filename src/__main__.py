import asyncio
from asyncio import CancelledError

import betterlogging as logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src import database
from src.config import TOKEN, TIME_TO_SLEEP
from src.handlers import setup_routers
from src.locale.russian import TRIAL_REMINDER

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

logging.basic_colorized_config(
    level=logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)
logger = logging.getLogger(__name__)


async def remind_about_trial():
    users_to_remind = await database.fetch_all("select telegramid from users where notified is false")

    if not users_to_remind or len(users_to_remind) == 0:
        logger.warning("All users are notified")
        return

    users_to_remind = [tgid[0] for tgid in users_to_remind]
    for tgid in users_to_remind:
        try:
            await database.execute(
                "update users set notified=true where telegramid=:telegramid",
                {"telegramid": tgid}
            )
            await bot.send_message(tgid, TRIAL_REMINDER)
        except TelegramBadRequest as exc:
            logger.warning(exc)
            continue


async def set_up_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(remind_about_trial, "interval", seconds=TIME_TO_SLEEP)
    scheduler.start()


async def main() -> None:
    try:
        router = setup_routers()
        dp.include_router(router)
        dp.startup.register(set_up_scheduler)

        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)

    except (KeyboardInterrupt, CancelledError):
        import traceback
        logger.warning(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
