from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src import database
from src.config import LINKS
from src.database import used_trial
from src.locale.russian import RETURN_BUTTON, USE_PROMOCODE


def apply_discount(price: int, discount: int) -> int:
    """Applies a discount to a given price."""
    return price - (price * discount // 100)


async def get_subscribe_kb(promocode: tuple = None) -> InlineKeyboardMarkup:
    """Generates a subscription options keyboard with optional promocode discount."""
    kb = InlineKeyboardBuilder()

    response = await database.fetch_all(
        "select duration, tarifplan, price from vocabularytarifs"
    )
    prices = {key: values for key, *values in response}
    percent = None

    if promocode:
        percent, tarif = promocode
        if tarif in prices:
            prices[tarif] = [f"💚 {prices[tarif][0]}", apply_discount(prices[tarif][1], percent)]

    for duration, price in prices.items():
        if "💚" in price[0]:
            text = f"{price[0]} — {price[1]} RUB (-{percent}%)"
        else:
            text = f"{price[0]} — {price[1]} RUB"
        callback_data = f"{price[1]}_{duration}_price"
        kb.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    kb.row(InlineKeyboardButton(text=USE_PROMOCODE, callback_data="promocode"))
    kb.row(InlineKeyboardButton(text=RETURN_BUTTON, callback_data="menu"))

    return kb.as_markup(resize_keyboard=True)


def get_subscription_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💳 Оформить подписку", callback_data="subscriptions"))
    kb.row(InlineKeyboardButton(text=RETURN_BUTTON, callback_data="menu"))
    return kb.as_markup(resize_keyboard=True)


def get_no_subscription_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💳 Оформить подписку", callback_data="subscriptions"))
    kb.row(InlineKeyboardButton(text="📞 Связаться с нами", url="https://t.me/whiterabbitsupport_bot"))
    kb.row(InlineKeyboardButton(text=RETURN_BUTTON, callback_data="client_subs"))
    return kb.as_markup(resize_keyboard=True)


async def get_client_area_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if await used_trial(user_id):
        kb.row(InlineKeyboardButton(text="💳 Оформить подписку", callback_data="subscriptions"))
    else:
        kb.row(InlineKeyboardButton(text="🎁 Тестовый период", callback_data="trial"))
    kb.row(InlineKeyboardButton(text="👤 Моя подписка", callback_data="profile"))
    kb.row(InlineKeyboardButton(text="📞 Связаться с нами", callback_data="support"))
    kb.row(InlineKeyboardButton(text="🐇 Скидка друзьям", callback_data="partnerprogram"))
    return kb.as_markup(resize_keyboard=True)


def get_welcome_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🚀 Начать работу", callback_data="menu"))
    return kb.as_markup(resize_keyboard=True)


def get_pay_kb(confirmation_url) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Оплатить через ЮKassa", url=confirmation_url))
    kb.row(InlineKeyboardButton(text="Назад к тарифам", callback_data="subscriptions"))
    return kb.as_markup(resize_keyboard=True)


def get_support_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="📖 Инструкция", callback_data="connection_guide"))
    kb.add(InlineKeyboardButton(text="🐇 О нас", callback_data="about"))
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="🎧 Связаться с поддержкой", url="https://t.me/whiterabbitsupport_bot"))
    kb.row(InlineKeyboardButton(text=RETURN_BUTTON, callback_data="menu"))
    return kb.as_markup(resize_keyboard=True)


def get_subs_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=RETURN_BUTTON, callback_data="subscriptions"))
    return kb.as_markup(resize_keyboard=True)


def get_return_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=RETURN_BUTTON, callback_data="menu"))
    return kb.as_markup(resize_keyboard=True)


def get_keys_kb(keys_list: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key in keys_list:
        kb.row(InlineKeyboardButton(
            text=f"🔑 {str(key[1])}",
            callback_data=f"key_{key[0]}"
        ))
    kb.row(InlineKeyboardButton(text="💳 Оформить подписку", callback_data="subscriptions"))
    kb.row(InlineKeyboardButton(text="⬅ Назад в меню", callback_data="menu"))
    return kb.as_markup()


def get_device_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for device, link in LINKS.items():
        emoji = "📱" if "ios" in device.lower() or "android" in device.lower() else "💻"
        kb.row(InlineKeyboardButton(text=f"{emoji} {device}", url=link))
    kb.row(InlineKeyboardButton(text="👍 Уже установлено", callback_data="menu"))
    return kb.as_markup()


def get_afterkey_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📖 Инструкция", callback_data="connection_guide"))
    kb.row(InlineKeyboardButton(text="⬅ На главную", callback_data="menu"))
    return kb.as_markup()


def get_partner_kb(invite_link) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="👥 Пригласить друга", url=invite_link))
    kb.row(InlineKeyboardButton(text="⬅ На главную", callback_data="menu"))
    return kb.as_markup()


def get_about_us_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="📜 Публичная оферта", callback_data="termsofservice"))
    kb.row(InlineKeyboardButton(text=RETURN_BUTTON, callback_data="support"))
    return kb.as_markup()
