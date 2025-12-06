import os
from pathlib import Path

from dotenv import load_dotenv
# from yookassa import Configuration

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
TOKEN = os.getenv("BOT_TOKEN", "")
DB_URL = os.getenv("DB_URL", "")

# Configuration.account_id = os.getenv("SHOP_ID")
# Configuration.secret_key = os.getenv("SECRET_KEY")
TIME_TO_SLEEP = 5400

TOS = BASE_DIR / "tos.pdf"
ADMINS = ""

# Marzban panels
PANEL_FREE = os.getenv("PANEL_FREE", "")
PANEL_PREMIUM = os.getenv("PANEL_PREMIUM", "")
PANEL_LOGIN = "rabbit"
PANEL_PASSWORD = "!0ngcarrot"

LINKS = {
    "iOS": "https://telegra.ph/VPN-dlya-IOS-instrukciya-03-07",
    "Android": "https://telegra.ph/VPN-dlya-Adnroid-instrukciya-03-07",
    "macOS": "https://github.com/hiddify/hiddify-next/releases/download/v0.17.12/Hiddify-MacOS.dmg",
    "Windows": "https://telegra.ph/VPN-dlya-Windows-instrukciya-03-07",
}
