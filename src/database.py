import datetime
from typing import LiteralString, Iterable, Any

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.config import DB_URL
from src.db.models import UserList

engine = create_async_engine(url=DB_URL)

session_factory = async_sessionmaker(engine)
session = session_factory()


async def close_database():
    await session.close()
    await engine.dispose()


async def execute(sql: LiteralString, params: Iterable[Any] | None = None, autocommit: bool = True) -> None:
    async with session_factory() as conn:
        sql = text(sql)
        sql = sql.bindparams(**params)
        await conn.execute(sql)
        if autocommit:
            await conn.commit()


async def fetch_value(sql: LiteralString, params: Iterable[Any] | None = None) -> any:
    async with session_factory() as conn:
        sql = text(sql)
        sql = sql.bindparams(**params)
        response = await conn.execute(sql)
        result = response.fetchone()
        return result[0] if result is not None else None


async def fetch_many(sql: LiteralString, params: Iterable[Any] | None = None) -> any:
    async with session_factory() as conn:
        sql = text(sql)
        if params:
            sql = sql.bindparams(**params)
        response = await conn.execute(sql)
        result = response.fetchmany()
        return result if result is not None else None


async def fetch_all(sql: LiteralString, params: Iterable[Any] | None = None) -> list[tuple] | None:
    async with session_factory() as conn:
        sql = text(sql)
        if params:
            sql = sql.bindparams(**params)
        response = await conn.execute(sql)
        result = response.fetchall()
        return result or None


async def fetch_one(sql: LiteralString, params: Iterable[Any] | None = None) -> tuple | None:
    async with session_factory() as conn:
        sql = text(sql)
        if params:
            sql = sql.bindparams(**params)
        response = await conn.execute(sql)
        row = response.fetchone()
        return row or None


async def used_trial(user_id: int) -> bool:
    async with engine.connect() as conn:
        sql_query = select(UserList.usedtrial).where(UserList.telegramid == user_id)
        result: UserList = (await conn.execute(sql_query)).fetchone()
        if not result[0]:
            return False
        return True


async def save_payment_method(user_id: int, payment_id: str, method: str) -> None:
    async with session_factory() as conn:
        stmt = text()
        stmt = stmt.bindparams(telegramid=user_id, paymentid=payment_id, type=method)
        await conn.execute(stmt)
        await conn.commit()


async def update_user_key(user_id: int, key_id: str):
    async with session_factory() as conn:
        stmt = text("delete from useraccess where telegramid=:telegramid and keyid=:keyid")
        stmt = stmt.bindparams(telegramid=user_id, keyid=key_id)
        await conn.execute(stmt)
        await conn.commit()


async def get_referal_state(user_id: int) -> bool:
    async with session_factory() as conn:
        query = text("select used from referrals where referralid=:telegramid")
        query = query.bindparams(telegramid=user_id)
        response = await conn.execute(query)
        result = response.fetchone()
        return result[0] if result is not None else False


async def disable_discount(user_id: int) -> None:
    async with session_factory() as conn:
        stmt = text("update referrals set used=True where referralid=:telegramid")
        stmt = stmt.bindparams(telegramid=user_id)
        await conn.execute(stmt)
        await conn.commit()


async def save_transaction(user_id: int, purchase: datetime, uuid: str, tarif: str, price: int) -> None:
    async with session_factory() as conn:
        stmt = text("INSERT INTO transactions (telegramid, issuedate, uuid, tarifplan, price)"
                    "VALUES (:telegramid, :issuedate, :uuid, :tarifplan, :price)")

        stmt = stmt.bindparams(telegramid=user_id, issuedate=purchase, uuid=uuid, tarifplan=tarif,
                               price=price)
        await conn.execute(stmt)
        await conn.commit()


async def clear_expired_keys() -> None:
    async with session_factory() as conn:
        stmt = text("TRUNCATE expireduseraccess")
        await conn.execute(stmt)
        await conn.commit()


async def is_user_exist(user_id: int) -> bool:
    async with session_factory() as conn:
        query = text("""SELECT telegramid FROM users WHERE telegramid=:telegramid""")
        query = query.bindparams(telegramid=user_id)
        cursor = await conn.execute(query)
        result = cursor.one_or_none()
        if result:
            return True
        return False


async def save_user_data(user_id: int, username: str, fullname: str, regdate: datetime) -> None:
    async with session_factory() as conn:
        stmt = text(f"""INSERT INTO users (telegramid, username, fullname, regdate)
            VALUES (:telegramid, :username, :fullname, :regdate)
            ON CONFLICT DO NOTHING;""")
        stmt = stmt.bindparams(telegramid=user_id, username=username, fullname=fullname, regdate=regdate)
        await conn.execute(stmt)
        await conn.commit()
