from datetime import datetime

import betterlogging as logging
import pytz

from src import database
from src.database import disable_discount
from src.db.methods import get_marzban_profile_db
from src.services import marzban_api, panel_premium

# Enable logging
logging.basic_colorized_config(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s")
logger = logging.getLogger(__name__)


def get_current_datetime() -> datetime:
    moscow_timezone = pytz.timezone("Europe/Moscow")
    current_time_in_moscow = datetime.now(moscow_timezone)
    current_datetime = current_time_in_moscow.replace(tzinfo=None)

    return current_datetime


async def get_all_users():
    return await database.fetch_all("select telegramid from users")


async def get_user_info(message):
    current_datetime = get_current_datetime()
    userdata = {
        'telegramid': message.from_user.id,
        'username': message.from_user.username,
        'fullname': message.from_user.full_name,
        'regdate': current_datetime
    }
    return userdata


async def process_transaction(user_id: int, uuid: str, price: int, desc: str):
    current_datetime = get_current_datetime()
    await database.save_transaction(user_id, current_datetime, uuid, desc, price)


async def payment_success_message(callback, days: int) -> dict:
    result = await get_marzban_profile_db(callback.from_user.id)
    result = await marzban_api.generate_marzban_subscription(result.vpn_id, days, panel_premium)

    await disable_discount(callback.from_user.id)
    return result
