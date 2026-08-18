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
# ASYNC RUNNER
# =========================================================

def run_async(coro):
    """
    Barcha Telethon coroutine'larini
    faqat bitta event loop orqali ishlatadi.
    """

    if LOOP.is_closed():
        raise RuntimeError(
            "Telegram event loop yopilgan."
        )

    return LOOP.run_until_complete(coro)


# =========================================================
# TELEGRAM AKKAUNTNI ULASH
# =========================================================

async def _start_client():

    if not telegram_client.is_connected():

        await telegram_client.start()

    return True


def start_client():
    """
    Telegram akkauntni yagona event loop orqali ulaydi.
    """

    return run_async(
        _start_client()
    )


# =========================================================
# AKKAUNT MA'LUMOTI
# =========================================================

async def _get_me():

    return await telegram_client.get_me()


def get_me():

    return run_async(
        _get_me()
    )


# =========================================================
# ULANISHNI TEKSHIRISH
# =========================================================

def is_connected():

    return telegram_client.is_connected()


# =========================================================
# CLIENTNI TO'XTATISH
# =========================================================

async def _disconnect_client():

    if telegram_client.is_connected():

        await telegram_client.disconnect()


def disconnect_client():

    if not LOOP.is_closed():

        try:
            run_async(
                _disconnect_client()
            )

        except Exception as e:

            print(
                "DISCONNECT ERROR:",
                repr(e)
            )
