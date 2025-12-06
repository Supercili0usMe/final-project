import datetime
from typing import Annotated

from sqlalchemy import ForeignKey, text, Column, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base

created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('Europe/Moscow', now())"))]


class VPNUsers(Base):
    __tablename__ = "useraccess"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=True)
    telegramid = Column(BigInteger, ForeignKey("users.telegramid", ondelete="CASCADE"))
    serverid: Mapped[int] = mapped_column(ForeignKey("servers.serverid", ondelete="CASCADE"))
    vpn_id: Mapped[str]
    paused: Mapped[bool]


class UserList(Base):
    __tablename__ = "users"

    telegramid = Column(BigInteger, primary_key=True, unique=True)
    username: Mapped[str | None]
    fullname: Mapped[str | None]
    regdate: Mapped[created_at]
    usedtrial: Mapped[bool]
    notified: Mapped[bool]
