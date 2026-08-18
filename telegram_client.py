import asyncio

from telethon import TelegramClient

from config import API_ID, API_HASH


# =========================================================
# YAGONA EVENT LOOP
# =========================================================

LOOP = asyncio.new_event_loop()

asyncio.set_event_loop(LOOP)


# =========================================================
# TELEGRAM CLIENT
# =========================================================

SESSION_NAME = "telegram_account"

telegram_client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    loop=LOOP
)


# =========================================================
# ASYNC ISHLATISH
# =========================================================

def run_async(coro):
    """
    Coroutine'ni doim bitta event loopda ishlatadi.
    """

    return LOOP.run_until_complete(coro)


# =========================================================
# TELEGRAM AKKAUNTNI ULASH
# =========================================================

def start_client():

    if telegram_client.is_connected():
        return True

    # MUHIM:
    # start() ni run_async() ichiga qo'ymaymiz.
    # Telethon login jarayonini o'zi boshqaradi.

    telegram_client.start()

    return True


# =========================================================
# AKKAUNT MA'LUMOTI
# =========================================================

def get_me():

    return run_async(
        telegram_client.get_me()
    )
