from telethon.tl.types import User, Chat, Channel


def normalize_username(value):
    value = value.strip()

    if value.startswith("@"):
        value = value[1:]

    return value


async def find_user(client, query):
    query = query.strip()

    if not query:
        return None

    if query.isdigit():
        try:
            return await client.get_entity(int(query))
        except Exception:
            return None

    username = normalize_username(query)

    try:
        return await client.get_entity(username)
    except Exception:
        return None


def format_user(user):
    if not isinstance(user, User):
        return None

    first_name = user.first_name or ""
    last_name = user.last_name or ""

    full_name = f"{first_name} {last_name}".strip()

    username = (
        f"@{user.username}"
        if user.username
        else "Username yo‘q"
    )

    return (
        "👤 <b>Foydalanuvchi topildi</b>\n\n"
        f"📝 Ism: <b>{full_name or 'Noma’lum'}</b>\n"
        f"👤 Username: <b>{username}</b>\n"
        f"🆔 ID: <code>{user.id}</code>"
    )


async def get_dialogs(client):
    dialogs = []

    async for dialog in client.iter_dialogs():

        entity = dialog.entity

        if isinstance(entity, (Chat, Channel)):
            dialogs.append({
                "id": entity.id,
                "title": dialog.title,
                "entity": entity
            })

    return dialogs
