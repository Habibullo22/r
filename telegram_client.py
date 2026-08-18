from telethon import TelegramClient
from config import API_ID, API_HASH


SESSION_NAME = "telegram_account"


def create_client():
    client = TelegramClient(
        SESSION_NAME,
        API_ID,
        API_HASH
    )

    return client
