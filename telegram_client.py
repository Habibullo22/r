import asyncio

from telethon import TelegramClient

from config import API_ID, API_HASH


# =========================================================
# BIRINCHI VA YAGONA EVENT LOOP
# =========================================================

LOOP = asyncio.new_event_loop()

asyncio.set_event_loop(LOOP)


# =========================================================
# TELEGRAM USER ACCOUNT
# =========================================================

SESSION_NAME = "telegram_account"


telegram_client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    loop=LOOP
)


# =========================================================
# ASYNC FUNKSIYANI ISHLATISH
# =========================================================

def run_async(coro):
    """
    Barcha Telethon coroutine'larini
    BIR xil event loop orqali ishlatadi.
    """

    return LOOP.run_until_complete(coro)


# =========================================================
# TELEGRAM AKKAUNTNI ULASH
# =========================================================

def start_client():

    if telegram_client.is_connected():
        return True

    run_async(
        telegram_client.start()
    )

    return True


# =========================================================
# AKKAUNT MA'LUMOTI
# =========================================================

def get_me():

    return run_async(
        telegram_client.get_me()
    )
