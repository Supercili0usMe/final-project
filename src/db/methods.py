import hashlib

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import DB_URL
from src.db.models import VPNUsers, UserList

engine = create_async_engine(DB_URL)


async def create_vpn_profile(tg_id: int):
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.telegramid == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
        if result != None:
            return
        hash = hashlib.md5(str(tg_id).encode()).hexdigest()
        sql_query = insert(VPNUsers).values(telegramid=tg_id, vpn_id=hash)
        await conn.execute(sql_query)
        await conn.commit()


async def get_marzban_profile_db(tg_id: int) -> VPNUsers:
    async with engine.connect() as conn:
        sql_query = select(VPNUsers).where(VPNUsers.telegramid == tg_id)
        result: VPNUsers = (await conn.execute(sql_query)).fetchone()
    return result


async def can_get_test_sub(tg_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(UserList).where(UserList.telegramid == tg_id)
        result: UserList = (await conn.execute(sql_query)).fetchone()
    return result.usedtrial


async def update_test_subscription_state(tg_id):
    async with engine.connect() as conn:
        sql_q = update(UserList).where(UserList.telegramid == tg_id).values(usedtrial=True)
        await conn.execute(sql_q)
        await conn.commit()
