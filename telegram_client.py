import asyncio

from telethon import TelegramClient
from config import API_ID, API_HASH


SESSION_NAME = "telegram_account"


# Bitta doimiy event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


# Telegram client
telegram_client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    loop=loop
)


def get_client():
    return telegram_client


def start_client():
    """
    Telegram akkauntini ulaydi.
    """
    loop.run_until_complete(
        telegram_client.start()
    )


def get_me():
    """
    Ulangan akkaunt ma'lumotlarini oladi.
    """
    return loop.run_until_complete(
        telegram_client.get_me()
    )


def run_async(coro):
    """
    Barcha Telegram async funksiyalarini
    bir xil event loop orqali ishlatadi.
    """
    return loop.run_until_complete(coro)
