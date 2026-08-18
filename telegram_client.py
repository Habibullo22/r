import os
from telethon import TelegramClient
from config import API_ID, API_HASH

SESSION_DIR = "sessions"
SESSION_NAME = "search_account"

os.makedirs(SESSION_DIR, exist_ok=True)

SESSION_FILE = os.path.join(
    SESSION_DIR,
    SESSION_NAME
)


def create_client():
    if not API_ID or not API_HASH:
        raise RuntimeError(
            "API_ID yoki API_HASH .env faylida topilmadi!"
        )

    return TelegramClient(
        SESSION_FILE,
        API_ID,
        API_HASH
    )


async def connect_client():
    client = create_client()

    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Telegram akkaunt hali ulanmagan.")
        print("📱 Akkauntni ulash kerak.")

    else:
        me = await client.get_me()

        print("================================")
        print("✅ TELEGRAM AKKAUNT ULANDI")
        print("================================")
        print(f"👤 Ism: {me.first_name}")
        print(f"🆔 ID: {me.id}")
        print(f"👤 Username: @{me.username}")
        print("================================")

    return client
