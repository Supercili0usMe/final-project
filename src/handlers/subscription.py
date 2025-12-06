import datetime
import math

import betterlogging as logging
from aiogram import Router, F
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hcode

from src import database
from src.db.methods import can_get_test_sub, get_marzban_profile_db, update_test_subscription_state
from src.locale.russian import SUBSCRIBE_TEXT, WEEK, ONE_MONTH, THREE_MONTH, ONE_YEAR, TOS_TEXT
from src.services import user_manager, payment, marzban_api, panel_free
from src.services.keyboards import get_subscribe_kb, get_pay_kb, get_afterkey_kb, get_subs_menu_kb

router = Router()

logging.basic_colorized_config(
    level=logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)
logger = logging.getLogger(__name__)

DURATION = {
    "7": [WEEK, 89],
    "30": [ONE_MONTH, 229],
    "90": [THREE_MONTH, 600],
    "365": [ONE_YEAR, 2200]
}


class Subscription(StatesGroup):
    enter_promocode = State()


def get_country_code(data: str) -> str:
    country_code = data.split("_", 1)[1]
    return country_code


@router.callback_query(F.data == "subscriptions")
async def send_sub_types(callback: CallbackQuery):
    await callback.message.edit_text(
        text=SUBSCRIBE_TEXT,
        reply_markup=await get_subscribe_kb()
    )


@router.callback_query(F.data.endswith("_price"))
async def pay_subscription(callback: CallbackQuery, state: FSMContext) -> None | bool:
    price, days = map(int, callback.data.split('_')[:2])
    final_price = await validate_final_price(callback.from_user.id, price)
    desc = f"{DURATION[str(days)][0]} {DURATION[str(days)][1]} RUB"

    payment_obj = await payment.create_invoice_yookassa(final_price, desc)
    if not payment_obj:
        return await handle_subscription_error(callback, "Возникли неполадки, приносим извинения за неудобства")

    logging.info(payment_obj.id)

    confirmation_url = payment_obj.confirmation.confirmation_url
    await callback.message.edit_text(text=TOS_TEXT, reply_markup=get_pay_kb(confirmation_url))

    status = await payment.poll_payment_status(callback.from_user.id, payment_obj.id, desc)

    if status:
        result = await user_manager.payment_success_message(callback, days)
        difference = datetime.datetime.fromtimestamp(result['expire']) - datetime.datetime.now()
        days_left = math.ceil(difference.total_seconds() / (60 * 60 * 24))
        data_limit = "неограничен" if not result['data_limit'] else result['data_limit'] / 1024 / 1024 / 1024
        await callback.message.answer("Информация о вашей премиальной подписке\n\n"
                                      f"Осталось дней: {days_left}\n"
                                      f"Осталось трафика: {data_limit}\n"
                                      "Скопируйте его нажатием и вставьте в приложение.\n\n"
                                      f"{hcode(result['subscription_url'])}",
                                      reply_markup=get_afterkey_kb())

    await state.clear()


async def validate_final_price(tgid: int, price: str):
    used_discount, referer = await payment.get_referral_info(tgid)

    if any(int(price) == default_price for _, default_price in DURATION.values()):
        if not used_discount:
            price = await payment.apply_referal_discount(price, referer)

    return price


async def handle_subscription_error(callback: CallbackQuery, error_message: str):
    await callback.answer(text=error_message, show_alert=True)


@router.message(F.text, Subscription.enter_promocode)
async def process_promocode(message: Message, state: FSMContext):
    try:
        user_input = message.text.replace(" ", "")
    except ValueError as exc:
        logger.exception(f"{exc}")
        return await message.answer("Неправильный промокод", reply_markup=get_subs_menu_kb())

    promocode = await database.fetch_one(
        "select discountpercent, tarifs from promocodes where name=:promocode",
        {"promocode": user_input.lower()}
    )
    if not promocode:
        await message.answer("Такого промокода нет", reply_markup=get_subs_menu_kb())
    else:
        await message.answer(text=SUBSCRIBE_TEXT + "\nПо промокоду за вами закреплена скидка на 💚 Этот тариф",
                             reply_markup=await get_subscribe_kb(promocode))
    await state.clear()


@router.callback_query(F.data == "promocode")
async def enter_promocode(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Subscription.enter_promocode)
    await callback.message.delete()
    await callback.message.answer("Введите промокод")


@router.callback_query(F.data == "trial")
async def test_subscription(callback: CallbackQuery):
    result = await can_get_test_sub(callback.from_user.id)
    if result:
        await callback.answer("Вы уже использовали пробный период", show_alert=True)
        return
    await callback.answer("Ваша подписка генерируется... ⌛", show_alert=True)
    await callback.bot.send_chat_action(chat_id=callback.from_user.id, action=ChatAction.TYPING)
    result = await get_marzban_profile_db(callback.from_user.id)
    result = await marzban_api.generate_test_subscription(result.vpn_id, panel_free)
    await update_test_subscription_state(callback.from_user.id)

    difference = datetime.datetime.fromtimestamp(result['expire']) - datetime.datetime.now()
    days_left = math.ceil(difference.total_seconds() / (60 * 60 * 24))
    data_limit = "неограничен" if not result['data_limit'] else result['data_limit'] / 1024 / 1024 / 1024

    await callback.message.answer(
        "Информация о вашей бесплатной подписке\n\n"
        f"Осталось дней: {days_left}\n"
        f"Осталось трафика: {data_limit} GB\n"
        f"Страна: Нидерланды 🇳🇱\n\n"
        f"Скопируйте его нажатием и вставьте в приложение.\n\n"
        f"{hcode(result['subscription_url'])}",
        reply_markup=get_afterkey_kb()
    )
