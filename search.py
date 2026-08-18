from telethon.tl.types import User, Chat, Channel


def clean_username(value):
    value = value.strip()

    if value.startswith("@"):
        value = value[1:]

    return value


async def find_user(client, query):
    """
    Username yoki Telegram ID orqali foydalanuvchini topadi.
    """

    query = query.strip()

    if not query:
        return None

    try:
        # ID
        if query.isdigit():
            return await client.get_entity(int(query))

        # Username
        username = clean_username(query)

        return await client.get_entity(username)

    except Exception as e:
        print("FIND USER ERROR:", e)
        return None


def format_user(user):
    """
    Foydalanuvchi profilini chiroyli formatlaydi.
    """

    if not isinstance(user, User):
        return "❌ Foydalanuvchi topilmadi."

    first_name = user.first_name or ""
    last_name = user.last_name or ""

    full_name = f"{first_name} {last_name}".strip()

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


async def get_my_chats(client):
    """
    Ulangan akkaunt ko‘ra oladigan dialoglarni oladi.
    """

    result = []

    async for dialog in client.iter_dialogs():

        entity = dialog.entity

        if isinstance(entity, (Chat, Channel)):

            result.append({
                "id": entity.id,
                "title": dialog.title,
                "entity": entity
            })

    return result


async def search_user_messages(client, user, limit_per_chat=30):
    """
    Ulangan akkaunt kira oladigan chatlarda
    foydalanuvchining mavjud xabarlarini qidiradi.
    """

    results = []

    try:

        dialogs = await get_my_chats(client)

        for dialog in dialogs:

            entity = dialog["entity"]

            try:

                messages = await client.get_messages(
                    entity,
                    limit=limit_per_chat,
                    from_user=user.id
                )

                if messages:

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
                    f"CHAT SEARCH ERROR "
                    f"{dialog['title']}: {e}"
                )

                continue

    except Exception as e:

        print("SEARCH MESSAGES ERROR:", e)

    return results


async def search_user_chats(client, user):
    """
    Foydalanuvchi mavjud bo‘lgan chatlar bo‘yicha
    API orqali tekshiradi.
    """

    found = []

    dialogs = await get_my_chats(client)

    for dialog in dialogs:

        entity = dialog["entity"]

        try:

            # Channel / supergroup
            if isinstance(entity, Channel):

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

                except Exception:
                    pass

            # Oddiy guruh
            elif isinstance(entity, Chat):

                try:

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

                except Exception:
                    pass

        except Exception:
            continue

    return found
