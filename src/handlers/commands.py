import datetime
import inspect

import betterlogging as logging
from aiogram import Router, Bot, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNotFound, TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.utils.markdown import hcode

from src import database
from src.config import ADMINS
from src.locale.russian import SUBSCRIBE_TEXT, NO_TRIAL_MAIN_MENU, HAS_TRIAL_MAIN_MENU
from src.services import user_manager
from src.services.keyboards import get_subscribe_kb, get_support_kb, get_client_area_kb

router = Router()

logging.basic_colorized_config(
    level=logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)
logger = logging.getLogger(__name__)


class Admin(StatesGroup):
    referal = State()
    announcement = State()
    chatid = State()
    whisper = State()
    promocode = State()
    key = State()


def admin_only():
    def inner_dec(func):
        async def wrapper(message: Message, *args, **kwargs):
            accepted_kwargs = {k: v for k, v in kwargs.items() if k in inspect.signature(func).parameters}
            user_id = message.from_user.id
            if user_id not in ADMINS:
                return await message.answer("У вас нет доступа к этой команде.")
            return await func(message, *args, **accepted_kwargs)

        return wrapper

    return inner_dec


@router.message(Command("subscriptions"))
async def send_sub_types(message: Message):
    await message.answer(text=SUBSCRIBE_TEXT, reply_markup=await get_subscribe_kb())


@router.message(Command("menu"))
async def send_main_menu(message: Message):
    if await database.used_trial(message.from_user.id):
        await message.answer(
            text=NO_TRIAL_MAIN_MENU,
            reply_markup=await get_client_area_kb(message.from_user.id)
        )
    else:
        await message.answer(
            text=HAS_TRIAL_MAIN_MENU,
            reply_markup=await get_client_area_kb(message.from_user.id)
        )


@router.message(Command("help"))
async def support(message: Message):
    await message.answer(text=f"Как мы можем вам помочь?", reply_markup=get_support_kb())


@router.message(Command('getid'))
@admin_only()
async def get_document_id(message: Message):
    if message.document:
        document_id = message.document.file_id
        await message.reply(f"The ID of the document is: {hcode(document_id)}")
    else:
        await message.reply("Please send a document with the /getid command.")


@router.message(F.text, Admin.referal)
async def create_referal(message: Message, state: FSMContext):
    referal = message.text.split(",")
    await database.execute(
        "insert into refrating (referrerlink, discountpercent) values (:referer, :discount) on conflict do nothing",
        {"referer": referal[0], "discount": int(referal[1])}
    )
    await message.answer(f"Реферальная ссылка со скидкой{referal[1]}%\n"
                         f"`https://t.me/{(await message.bot.get_me()).username}?start={referal[0]}`",
                         parse_mode="MarkdownV2")
    await state.clear()


@router.message(Command("referal"))
@admin_only()
async def referal_command_handler(message: Message, state: FSMContext):
    await state.set_state(Admin.referal)
    await message.answer(
        "Введи название реферального кода и сумму скидки через запятую\n"
        "Например: `superdiscount, 100`",
        parse_mode="MarkdownV2"
    )


@router.message(F.text, Admin.announcement)
async def announce_send(message: Message, bot: Bot, state: FSMContext):
    users = await user_manager.get_all_users()
    ids = [t[0] for t in users]
    for user_id in ids:
        try:
            await bot.send_message(user_id, message.md_text, parse_mode="MarkdownV2")
        except TelegramBadRequest:
            await message.answer(f"ID {user_id} не существует")
        except TelegramNotFound:
            await message.answer(f"Вероятно, пользователь {user_id} не общался с ботом.")
        except TelegramForbiddenError:
            await message.answer(f"Пользователь {user_id} заблокировал бота.")
    await message.answer("Сообщение анонсировано!")
    await state.clear()


@router.message(Command('announce'))
@admin_only()
async def annouce(message: Message, state: FSMContext):
    await message.answer("Отправь сообщение для анонса")
    await state.set_state(Admin.announcement)


@router.message(Admin.whisper)
async def process_message(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_ids = [i for i in data['chatid'].split(",")]

    for user_id in user_ids:
        user_id = user_id.strip()
        try:
            await bot.send_message(user_id, message.md_text, parse_mode="MarkdownV2")
        except TelegramBadRequest:
            await message.answer(f"ID {user_id} не существует")
        except TelegramNotFound:
            await message.answer(f"Вероятно, пользователь {user_id} не общался с ботом.")
        except TelegramForbiddenError:
            await message.answer(f"Пользователь {user_id} заблокировал бота.")
    await message.answer("✅ Рассылка приватных сообщений завершена.")
    await state.clear()


@router.message(Admin.chatid)
async def process_user_ids(message: Message, state: FSMContext):
    await state.update_data(chatid=message.text)
    await message.answer("А теперь напиши текст, который должен быть отправлен")
    await state.set_state(Admin.whisper)


@router.message(Command("whisper"))
@admin_only()
async def send_message_to_users(message: Message, state: FSMContext):
    await message.answer(
        "Укажи через запятую ID пользователей, которым будет отправлено сообщение\n"
        "Например: `93213,13913818,3132513,13123245`",
        parse_mode="MarkdownV2"
    )
    await state.set_state(Admin.chatid)


@router.message(F.text, Admin.promocode)
async def handle_promocode(message: Message, state: FSMContext):
    try:
        promocode, discount, exp_date, tarif = message.text.lower().replace(" ", "").split(',')
        exp_date = datetime.datetime.strptime(exp_date, "%d.%m.%Y").date()
    except ValueError as exc:
        logger.exception(f"{exc}")
        return await message.answer(
            "Обкак в формате\\.\nПиши так: `промокод, процент, дата_истечения, тарифный_план`\n"
            "Процент — число без знака\\.\n"
            "Тарифный план — длительность \\(7, 30, 90, 365\\)\\.\n"
            "Дата истечения в формате `дд.мм.гггг`\n\n"
            "Пример: `SUPER, 50, 29.02.2028, 90`",
            parse_mode=ParseMode.MARKDOWN_V2)

    await database.execute(
        """
        INSERT INTO promocodes(name, expdate, discountpercent, tarifs) 
        VALUES (:name, :expdate, :percent, :tarif) 
        ON CONFLICT DO NOTHING
        """,
        {"name": promocode.lower(), "expdate": exp_date, "percent": int(discount), "tarif": int(tarif)}
    )
    await message.react([ReactionTypeEmoji(emoji="👍")])
    await state.clear()


@router.message(Command("promocode"))
@admin_only()
async def create_promocode(message: Message, state: FSMContext):
    await state.set_state(Admin.promocode)
    await message.answer("Введите промокод")
