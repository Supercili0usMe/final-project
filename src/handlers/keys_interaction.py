from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from src import database

router = Router()


class KeyData(StatesGroup):
    keyname = State()


def premium_only(func):
    async def wrapper(callback: CallbackQuery):
        entry_id = int(callback.data.split('_')[0])

        keytype = await database.fetch_value(
            "select keytype from useraccess where id=:entry_id",
            {"entry_id": entry_id}
        )

        if keytype.lower() == "free":
            return await callback.answer(text="Функция доступна на платной подписке", show_alert=True)

        await func(callback)

    return wrapper
