import datetime
import logging
import math

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.markdown import hcode

from src import config, database
from src.config import LINKS
from src.locale.russian import ABOUT_US, HAS_TRIAL_MAIN_MENU, NO_TRIAL_MAIN_MENU, OUTLINE_PRESENCE, PARTNER_TEXT
from src.services import marzban_api, panel_premium, panel_free
from src.services.keyboards import get_support_kb, get_client_area_kb, get_about_us_kb, get_device_kb, get_partner_kb, \
    get_afterkey_kb, get_return_menu_kb

router = Router()


def get_device_type(device: str) -> str:
    return LINKS.get(device.split("_")[-1], "Invalid device")


async def create_referal_link(chat_id):
    await database.execute(
        """insert into refrating (referrerlink, discountpercent) 
        values (:referer, :discount) on conflict do nothing""",
        {"referer": chat_id, "discount": 10}
    )


@router.callback_query(F.data == "about")
async def send_tos(callback: CallbackQuery):
    await callback.message.edit_text(text=ABOUT_US, reply_markup=get_about_us_kb())


@router.callback_query(F.data.startswith("menu"))
async def start_dialog(callback: CallbackQuery):
    if await database.used_trial(callback.from_user.id):
        await callback.message.edit_text(
            text=NO_TRIAL_MAIN_MENU,
            reply_markup=await get_client_area_kb(callback.from_user.id)
        )
    else:
        await callback.message.edit_text(
            text=HAS_TRIAL_MAIN_MENU,
            reply_markup=await get_client_area_kb(callback.from_user.id)
        )


@router.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await callback.message.edit_text(text=f"Как мы можем Вам помочь?", reply_markup=get_support_kb())


@router.callback_query(F.data == "profile")
async def fetch_active_subscriptions(callback: CallbackQuery):
    user = None
    try:
        user = await marzban_api.get_marzban_profile(callback.from_user.id, panel_premium)
        if not user:
            user = await marzban_api.get_marzban_profile(callback.from_user.id, panel_free)
    except Exception as e:
        logging.info("Can't fetch user")
    if user is None:
        await callback.message.edit_text(
            "У вас ещё нет VPN профиля\n"
            "Убедитесь в качестве нашего сервиса, выбрав 🎁 Тестовый период\n\n"
            "Откройте для себя безопасность подключения из разных стран, оформив премиальную подписку, а мы позаботимся об остальном.",
            reply_markup=get_return_menu_kb()
        )
        return
    difference = datetime.datetime.fromtimestamp(user['expire']) - datetime.datetime.now()
    days_left = math.ceil(difference.total_seconds() / (60 * 60 * 24))
    data_limit = "неограничен" if not user['data_limit'] else user['data_limit'] / 1024 / 1024 / 1024
    await callback.message.edit_text("Информация о вашей подписке\n\n"
                                     f"Осталось дней: {days_left}\n"
                                     f"Осталось трафика: {data_limit} GB\n\n"
                                     f"🔑 Скопируйте ключ нажатием и вставьте в приложение.\n\n"
                                     f"{hcode(user['subscription_url'])}", reply_markup=get_afterkey_kb())


@router.callback_query(F.data == "termsofservice")
async def send_tos(callback: CallbackQuery):
    tos_file = FSInputFile(path=config.TOS, filename="Публичная оферта.pdf")
    await callback.message.answer_document(document=tos_file)


@router.message(F.pinned_message)
async def clean_chat(message: Message):
    await message.delete()


@router.callback_query(F.data == "connection_guide")
async def ask_about_outline(callback: CallbackQuery):
    await callback.message.edit_text(
        text=OUTLINE_PRESENCE,
        reply_markup=get_device_kb()
    )


@router.callback_query(F.data == "partnerprogram")
async def invite_friend_handler(callback: CallbackQuery, bot: Bot):
    await create_referal_link(callback.from_user.id)

    invite_link = f"https://telegram.me/share/url?url=https://t.me/{(await bot.get_me()).username}?start={callback.from_user.id}"
    referer = hcode(f"https://t.me/{(await bot.get_me()).username}?start={callback.from_user.id}")

    await callback.message.edit_text(
        text=PARTNER_TEXT + referer,
        reply_markup=get_partner_kb(invite_link)
    )
