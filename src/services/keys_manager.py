import logging

import pytz
from beautiful_date import days, D

from src import database


async def key_freeze(entryid: int):
    issuedate, duration, keyid, keyapi = await database.fetch_one(
        "select issuedate, duration, keyid, api from useraccess where id=:id",
        {"id": entryid}
    )
    logging.info(f"Freezing {entryid}...")
    expire = issuedate.date() + duration * days
    today = D.today()
    difference = expire - today

    await database.execute(
        "update useraccess set paused=true, duration=:days WHERE id=:id",
        {"days": difference.days, "id": entryid}
    )


async def key_unfreeze(entryid: int):
    logging.info(f"Unfreezing {entryid}...")

    keyid, keyapi = await database.fetch_one(
        "select keyid, api from useraccess where id=:id",
        {"id": entryid}
    )
    await database.execute(
        "update useraccess set paused=false WHERE id=:id",
        {"id": entryid}
    )


def get_current_datetime():
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_datetime = D.now(moscow_tz)
    current_datetime = current_datetime.replace(tzinfo=None)
    return current_datetime
