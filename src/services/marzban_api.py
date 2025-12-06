import time

import aiohttp
import requests

from src.config import PANEL_FREE, PANEL_LOGIN, PANEL_PASSWORD, PANEL_PREMIUM
from src.db.methods import get_marzban_profile_db

PROTOCOLS = {
    "vmess": [
        {},
        ["VMess TCP"]
    ],
    "vless": [
        {
            "flow": "xtls-rprx-vision"
        },
        ["VLESS TCP REALITY"]
    ],
    "trojan": [
        {},
        ["Trojan Websocket TLS"]
    ],
    "shadowsocks": [
        {},
        ["Shadowsocks TCP"]
    ]
}


class Marzban:
    def __init__(self, address) -> None:
        self.address = address
        self.login = PANEL_LOGIN
        self.passwd = PANEL_PASSWORD
        self.token = None

    async def _send_request(self, method, path, headers=None, data=None) -> dict | list:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, self.address + path, headers=headers, json=data) as resp:
                if 200 <= resp.status < 300:
                    body = await resp.json()
                    return body
                else:
                    raise Exception(f"Error: {resp.status}; Body: {await resp.text()}; Data: {data}")

    def get_token(self) -> str:
        # data = {
        #     "username": self.login,
        #     "password": self.passwd
        # }
        # resp = requests.post(self.address + "/api/admin/token", data=data).json()
        # self.token = resp["access_token"]
        # return self.token
        return ""

    async def get_user(self, username) -> dict:
        # headers = {
        #     'Authorization': f"Bearer {self.token}"
        # }
        # resp = await self._send_request("GET", f"/api/user/{username}", headers=headers)
        # return resp
        return {}

    async def get_users(self) -> dict:
        # headers = {
        #     'Authorization': f"Bearer {self.token}"
        # }
        # resp = await self._send_request("GET", "/api/users", headers=headers)
        # return resp
        return {}

    async def add_user(self, data) -> dict:
        # headers = {
        #     'Authorization': f"Bearer {self.token}"
        # }
        # resp = await self._send_request("POST", "/api/user", headers=headers, data=data)
        # return resp
        return {}

    async def modify_user(self, username, data) -> dict:
        # headers = {
        #     'Authorization': f"Bearer {self.token}"
        # }
        # resp = await self._send_request("PUT", f"/api/user/{username}", headers=headers, data=data)
        # return resp
        return {}


def get_protocols() -> dict:
    proxies = {}
    inbounds = {}

    for proto in ["vless"]:
        name = proto.lower()
        if name not in PROTOCOLS:
            continue
        proxies[name] = PROTOCOLS[name][0]
        inbounds[name] = PROTOCOLS[name][1]
    return {
        "proxies": proxies,
        "inbounds": inbounds
    }


# Инициализация экземпляров Marzban для двух разных веб-панелей
panel_free = Marzban(PANEL_FREE)
panel_premium = Marzban(PANEL_PREMIUM)

# Получение токенов для каждой панели
token_free = panel_free.get_token()
token_premium = panel_premium.get_token()

ps = get_protocols()


async def check_if_user_exists(name: str, panel_instance: Marzban) -> bool:
    try:
        await panel_instance.get_user(name)
        return True
    except Exception as exc:
        print(f"{exc}")
        return False


async def get_marzban_profile(tg_id: int, panel_instance: Marzban):
    # result = await get_marzban_profile_db(tg_id)
    # res = await check_if_user_exists(result.vpn_id, panel_instance)
    # if not res:
        return None
    # return await panel_instance.get_user(result.vpn_id)


async def generate_test_subscription(username: str, panel_instance: Marzban):
    res = await check_if_user_exists(username, panel_instance)
    if res:
        user = await panel_instance.get_user(username)
        user['status'] = 'active'
        if user['expire'] < time.time():
            user['expire'] = get_test_subscription(72)
        else:
            user['expire'] += get_test_subscription(72, True)
        result = await panel_instance.modify_user(username, user)
    else:
        user = {
            'username': username,
            'proxies': ps["proxies"],
            'inbounds': ps["inbounds"],
            'expire': get_test_subscription(72),
            'data_limit': 10 * 1024 * 1024 * 1024,
            'data_limit_reset_strategy': "no_reset",
        }
        result = await panel_instance.add_user(user)
    return result


async def generate_marzban_subscription(username: str, days: int, panel_instance: Marzban):
    res = await check_if_user_exists(username, panel_instance)
    if res:
        user = await panel_instance.get_user(username)
        user['status'] = 'active'
        if user['expire'] < time.time():
            user['expire'] = get_subscription_end_date(days)
        else:
            user['expire'] += get_subscription_end_date(days, True)
        result = await panel_instance.modify_user(username, user)
    else:
        user = {
            "username": username,
            "proxies": ps["proxies"],
            "inbounds": ps["inbounds"],
            "expire": get_subscription_end_date(days),
            "data_limit": 0,
            "data_limit_reset_strategy": "no_reset",
        }
        result = await panel_instance.add_user(user)
    return result


def get_test_subscription(hours: int, additional=False) -> int:
    return (0 if additional else int(time.time())) + 60 * 60 * hours


def get_subscription_end_date(days: int, additional=False) -> int:
    return (0 if additional else int(time.time())) + 60 * 60 * 24 * days
