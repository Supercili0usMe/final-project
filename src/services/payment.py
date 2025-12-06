import asyncio
import logging
import uuid

# from yookassa import Payment

from src import database
from src.services.user_manager import process_transaction


async def apply_referal_discount(default_price: str, referer: str) -> str:
    percent = await database.fetch_value(
        "select discountpercent from refrating where referrerlink=:referer",
        {"referer": referer}
    )
    whole_number_part = int(default_price.split(".")[0])
    discounted_value = whole_number_part * (percent / 100)
    new_price = whole_number_part - discounted_value
    return "{:.2f}".format(new_price)


async def poll_payment_status(tg_id: int, payment_id: str, desc: str) -> bool:
    # await asyncio.sleep(8)
    # try:
    #     payment = Payment.find_one(payment_id)
    #     if payment.paid and payment.status == "succeeded":
    #         await process_transaction(tg_id, payment.id, int(payment.amount.value), desc)
    #         return True
    #     if payment.status == "canceled":
    #         return False
    #     return await poll_payment_status(tg_id, payment_id, desc)
    # except Exception as exc:
    #     logging.info(f"{exc}")
    return True


async def get_referral_info(user_id: int):
    referral_info = await database.fetch_one(
        "SELECT used, referrerlink FROM referrals WHERE referralid=:telegramid",
        {"telegramid": user_id}
    )
    return referral_info or (True, None)


async def create_invoice_yookassa(price: str, desc: str):
    # idempotence_key = str(uuid.uuid4())
    # try:
    #     response = Payment.create({
    #         "amount": {
    #             "value": price,
    #             "currency": "RUB"
    #         },
    #         "confirmation": {
    #             "type": "redirect",
    #             "return_url": "https://t.me/whiterabbitvpn_bot"
    #         },
    #         "description": desc,
    #         "receipt": {
    #             "customer": {
    #                 "email": "info.veseles@gmail.com"
    #             },
    #             "items": [
    #                 {
    #                     "description": desc,
    #                     "quantity": "1.00",
    #                     "amount": {
    #                         "value": price,
    #                         "currency": "RUB"
    #                     },
    #                     "vat_code": "2",
    #                     "payment_mode": "full_prepayment",
    #                     "payment_subject": "commodity"
    #                 }
    #             ]
    #         },
    #         "capture": True
    #     }, idempotence_key)
    #     return response
    # except Exception as exc:
    #     logging.exception(f"{exc}")
    return ""
