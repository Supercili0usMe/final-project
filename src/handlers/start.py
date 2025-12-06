import logging

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src import database
from src.db.methods import create_vpn_profile
from src.locale.russian import WELCOME
from src.services import user_manager
from src.services.keyboards import get_welcome_kb

router = Router()


async def register_new_user(message):
    user = await user_manager.get_user_info(message)
    await database.save_user_data(user['telegramid'], user['username'], user['fullname'], user['regdate'])
    await create_vpn_profile(message.from_user.id)


async def handle_referral_link(user_id, referral_code):
    referral = await database.fetch_one("SELECT * FROM refrating WHERE referrerlink=:referer",
                                        {"referer": referral_code})
    if referral:
        await database.execute(
            "INSERT INTO referrals(referrerlink, referralid) VALUES (:referrerlink, :referralid) ON CONFLICT DO NOTHING",
            {"referrerlink": referral_code, "referralid": user_id}
        )


async def send_welcome_message(message):
    await message.answer(text=WELCOME, reply_markup=get_welcome_kb())


@router.message(CommandStart(deep_link=True))
async def command_start_handler(message: Message, command: CommandObject, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(welcome=True)
    if not await database.is_user_exist(user_id):
        await register_new_user(message)
        await handle_referral_link(user_id, command.args)
        logging.info(f"Registered {user_id} with referal {command.args}")

    await send_welcome_message(message)


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(welcome=True)
    if not await database.is_user_exist(user_id):
        await register_new_user(message)
        logging.info(f"Registered {message.from_user.id}")

    await send_welcome_message(message)
