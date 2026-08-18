from telethon.tl.types import User, Chat, Channel


# =========================================================
# USERNAME TOZALASH
# =========================================================

def clean_username(value):
    value = (value or "").strip()

    if value.startswith("@"):
        value = value[1:]

    return value


# =========================================================
# USER TOPISH
# =========================================================

async def find_user(client, query):

    query = (query or "").strip()

    if not query:
        return None

    try:

        # Telegram ID
        if query.isdigit():
            return await client.get_entity(int(query))

        # Username
        username = clean_username(query)

        if not username:
            return None

        return await client.get_entity(username)

    except Exception as e:

        print("FIND USER ERROR:", repr(e))

        return None


# =========================================================
# USER FORMAT
# =========================================================

def format_user(user):

    if not isinstance(user, User):
        return "❌ Foydalanuvchi topilmadi."

    first_name = user.first_name or ""
    last_name = user.last_name or ""

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    username = (
        f"@{user.username}"
        if user.username
        else "Username yo‘q"
    )

    return (
        "👤 <b>FOYDALANUVCHI</b>\n\n"
        f"📝 Ism: <b>{full_name or 'Noma’lum'}</b>\n"
        f"👤 Username: <b>{username}</b>\n"
        f"🆔 ID: <code>{user.id}</code>"
    )


# =========================================================
# CHATLARNI OLISH
# =========================================================

async def get_my_chats(client):

    result = []

    try:

        async for dialog in client.iter_dialogs():

            entity = dialog.entity

            # Faqat guruh va kanallar
            if isinstance(entity, (Chat, Channel)):

                # Channel ichidan haqiqiy kanal/supergroup
                # ekanligini saqlab qolamiz
                if isinstance(entity, Channel):

                    if getattr(
                        entity,
                        "broadcast",
                        False
                    ):

                        chat_type = "channel"

                    else:

                        chat_type = "group"

                else:

                    chat_type = "group"

                result.append({
                    "id": entity.id,
                    "title": dialog.title or "Noma’lum",
                    "entity": entity,
                    "type": chat_type
                })

    except Exception as e:

        print(
            "GET CHATS ERROR:",
            repr(e)
        )

    return result


# =========================================================
# GURUHLARNI TEKSHIRISH
# =========================================================

async def search_user_groups(
    client,
    user,
    progress_callback=None
):

    found = []

    try:

        dialogs = await get_my_chats(client)

        groups = [
            dialog
            for dialog in dialogs
            if dialog["type"] == "group"
        ]

        total = len(groups)

        checked = 0

        for dialog in groups:

            entity = dialog["entity"]

            try:

                # Telegram API orqali mavjud
                # permission ma'lumotini tekshirish

                participant = await client.get_permissions(
                    entity,
                    user
                )

                if participant:

                    found.append({
                        "title": dialog["title"],
                        "entity": entity,
                        "type": "group"
                    })

            except Exception as e:

                print(
                    f"GROUP ERROR "
                    f"{dialog['title']}: {e}"
                )

            checked += 1

            # REAL PROGRESS
            if progress_callback:

                await progress_callback(
                    checked,
                    total
                )

    except Exception as e:

        print(
            "GROUP SEARCH ERROR:",
            repr(e)
        )

    return found


# =========================================================
# KANALLARNI TEKSHIRISH
# =========================================================

async def search_user_channels(
    client,
    user,
    progress_callback=None
):

    found = []

    try:

        dialogs = await get_my_chats(client)

        channels = [
            dialog
            for dialog in dialogs
            if dialog["type"] == "channel"
        ]

        total = len(channels)

        checked = 0

        for dialog in channels:

            entity = dialog["entity"]

            try:

                participant = await client.get_permissions(
                    entity,
                    user
                )

                if participant:

                    found.append({
                        "title": dialog["title"],
                        "entity": entity,
                        "type": "channel"
                    })

            except Exception as e:

                print(
                    f"CHANNEL ERROR "
                    f"{dialog['title']}: {e}"
                )

            checked += 1

            # REAL PROGRESS
            if progress_callback:

                await progress_callback(
                    checked,
                    total
                )

    except Exception as e:

        print(
            "CHANNEL SEARCH ERROR:",
            repr(e)
        )

    return found


# =========================================================
# UMUMIY CHAT QIDIRUV
# =========================================================

async def search_user_chats(
    client,
    user
):

    found = []

    try:

        dialogs = await get_my_chats(client)

        for dialog in dialogs:

            entity = dialog["entity"]

            try:

                participant = await client.get_permissions(
                    entity,
                    user
                )

                if participant:

                    found.append({
                        "title": dialog["title"],
                        "entity": entity,
                        "type": dialog["type"]
                    })

            except Exception as e:

                print(
                    f"CHAT ERROR "
                    f"{dialog['title']}: {e}"
                )

                continue

    except Exception as e:

        print(
            "CHAT SEARCH ERROR:",
            repr(e)
        )

    return found


# =========================================================
# USER XABARLARINI QIDIRISH
# =========================================================

async def search_user_messages(
    client,
    user,
    limit_per_chat=30,
    progress_callback=None
):

    results = []

    try:

        dialogs = await get_my_chats(client)

        total = len(dialogs)

        checked = 0

        for dialog in dialogs:

            entity = dialog["entity"]

            try:

                messages = await client.get_messages(
                    entity,
                    limit=limit_per_chat,
                    from_user=user.id
                )

                valid_messages = [
                    message
                    for message in messages
                    if message is not None
                ]

                if valid_messages:

                    results.append({
                        "title": dialog["title"],
                        "entity": entity,
                        "messages": valid_messages
                    })

            except Exception as e:

                print(
                    f"MESSAGE ERROR "
                    f"{dialog['title']}: {e}"
                )

            checked += 1

            # REAL PROGRESS
            if progress_callback:

                await progress_callback(
                    checked,
                    total
                )

    except Exception as e:

        print(
            "MESSAGE SEARCH ERROR:",
            repr(e)
        )

    return results


# =========================================================
# REAKSIYALAR
# =========================================================

async def search_user_reactions(
    client,
    user,
    progress_callback=None
):

    """
    Telegram API ruxsat bergan mavjud
    reaksiya ma'lumotlarini tekshiradi.

    Muhim:
    Telegram boshqa foydalanuvchining barcha
    reaksiyalarini global tarzda beradigan API
    bermaydi.
    """

    results = []

    try:

        dialogs = await get_my_chats(client)

        total = len(dialogs)

        checked = 0

        for dialog in dialogs:

            entity = dialog["entity"]

            try:

                # So'nggi xabarlarni ko'ramiz.
                # Faqat mavjud reaksiya ma'lumotlari olinadi.

                messages = await client.get_messages(
                    entity,
                    limit=50
                )

                for message in messages:

                    if not message:
                        continue

                    reactions = getattr(
                        message,
                        "reactions",
                        None
                    )

                    if not reactions:
                        continue

                    results.append({
                        "title": dialog["title"],
                        "message_id": message.id,
                        "reactions": reactions
                    })

            except Exception as e:

                print(
                    f"REACTION ERROR "
                    f"{dialog['title']}: {e}"
                )

            checked += 1

            if progress_callback:

                await progress_callback(
                    checked,
                    total
                )

    except Exception as e:

        print(
            "REACTION SEARCH ERROR:",
            repr(e)
        )

    return results
