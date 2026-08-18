# search.py

from telethon.tl.types import User, Channel, Chat
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.messages import SearchGlobalRequest


# =========================================================
# YORDAMCHI
# =========================================================

def clean_query(value):
    return (value or "").strip()


def clean_username(value):
    value = clean_query(value)

    if value.startswith("@"):
        value = value[1:]

    return value


def unique_by_id(items):
    result = []
    seen = set()

    for item in items:
        item_id = getattr(item, "id", None)

        if item_id is None:
            continue

        if item_id in seen:
            continue

        seen.add(item_id)
        result.append(item)

    return result


# =========================================================
# 1. FOYDALANUVCHI / PROFIL
# =========================================================

async def find_user(client, query):

    query = clean_query(query)

    if not query:
        return None

    # -----------------------------------------------------
    # TELEGRAM ID
    # -----------------------------------------------------

    if query.isdigit():

        try:
            entity = await client.get_entity(int(query))

            if isinstance(entity, User):
                return entity

        except Exception as e:
            print("ID SEARCH:", repr(e))

    # -----------------------------------------------------
    # USERNAME
    # -----------------------------------------------------

    username = clean_username(query)

    if username:

        try:
            entity = await client.get_entity(username)

            if isinstance(entity, User):
                return entity

        except Exception as e:
            print("USERNAME SEARCH:", repr(e))

    # -----------------------------------------------------
    # TELEGRAM CONTACT SEARCH
    # -----------------------------------------------------

    try:

        result = await client(
            SearchRequest(
                q=query,
                limit=100
            )
        )

        for user in result.users:

            if not isinstance(user, User):
                continue

            # Username aniq moslik
            if user.username:

                if user.username.lower() == username.lower():
                    return user

            # Ism bo'yicha moslik
            full_name = (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip().lower()

            if query.lower() in full_name:
                return user

    except Exception as e:

        print(
            "CONTACT SEARCH ERROR:",
            repr(e)
        )

    return None


# =========================================================
# PROFIL FORMAT
# =========================================================

def format_user(user):

    if not isinstance(user, User):

        return (
            "❌ <b>FOYDALANUVCHI TOPILMADI</b>"
        )

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

    verified = (
        "✅ Ha"
        if getattr(user, "verified", False)
        else "❌ Yo‘q"
    )

    premium = (
        "✅ Ha"
        if getattr(user, "premium", False)
        else "❌ Yo‘q"
    )

    bot_status = (
        "🤖 Bot"
        if getattr(user, "bot", False)
        else "👤 Oddiy akkaunt"
    )

    return (
        "👤 <b>FOYDALANUVCHI</b>\n\n"

        f"📝 Ism: "
        f"<b>{full_name or 'Noma’lum'}</b>\n"

        f"👤 Username: "
        f"<b>{username}</b>\n"

        f"🆔 ID: "
        f"<code>{user.id}</code>\n"

        f"☑️ Tasdiqlangan: "
        f"<b>{verified}</b>\n"

        f"⭐ Premium: "
        f"<b>{premium}</b>\n"

        f"📱 Turi: "
        f"<b>{bot_status}</b>"
    )


# =========================================================
# 2. KANALLARNI HAQIQIY QIDIRISH
# =========================================================

async def search_channels(client, query, limit=100):

    query = clean_query(query)

    if not query:
        return []

    channels = []

    try:

        # Telegram global public qidiruvi
 response = await client(
    SearchGlobalRequest(
        q=query,
        filter=None,
        min_date=None,
        max_date=None,
        offset_id=0,
        offset_rate=0,
        limit=limit
    )
        )

        for chat in response.chats:

            if not isinstance(chat, Channel):
                continue

            # Megagroup = guruh.
            # Shuning uchun faqat channel.
            if getattr(chat, "megagroup", False):
                continue

            channels.append(chat)

    except Exception as e:

        print(
            "CHANNEL SEARCH ERROR:",
            repr(e)
        )

    return unique_by_id(channels)


# =========================================================
# KANALLAR FORMAT
# =========================================================

def format_channels(channels, limit=50):

    if not channels:

        return (
            "📢 <b>KANALLAR</b>\n\n"
            "❌ Mos public kanal topilmadi."
        )

    text = (
        "📢 <b>KANALLAR</b>\n\n"
    )

    for i, channel in enumerate(
        channels[:limit],
        1
    ):

        title = (
            getattr(
                channel,
                "title",
                None
            )
            or "Noma’lum"
        )

        username = getattr(
            channel,
            "username",
            None
        )

        username_text = (
            f"@{username}"
            if username
            else "Username yo‘q"
        )

        text += (
            f"{i}. <b>{title}</b>\n"
            f"   👤 {username_text}\n"
            f"   🆔 <code>{channel.id}</code>\n\n"
        )

    return text


# =========================================================
# 3. GURUHLARNI HAQIQIY QIDIRISH
# =========================================================

async def search_groups(client, query, limit=100):

    query = clean_query(query)

    if not query:
        return []

    groups = []

    try:

        response = await client(
            SearchGlobalRequest(
                q=query,
                filter=None,
                min_date=None,
                max_date=None,
                offset_id=0,
                offset_rate=0,
                max_id=0,
                min_id=0,
                limit=limit
            )
        )

        for chat in response.chats:

            # Supergroup
            if isinstance(chat, Channel):

                if getattr(
                    chat,
                    "megagroup",
                    False
                ):
                    groups.append(chat)

            # Eski oddiy group
            elif isinstance(chat, Chat):

                groups.append(chat)

    except Exception as e:

        print(
            "GROUP SEARCH ERROR:",
            repr(e)
        )

    return unique_by_id(groups)


# =========================================================
# GURUHLAR FORMAT
# =========================================================

def format_groups(groups, limit=50):

    if not groups:

        return (
            "👥 <b>GURUHLAR</b>\n\n"
            "❌ Mos public guruh topilmadi."
        )

    text = (
        "👥 <b>GURUHLAR</b>\n\n"
    )

    for i, group in enumerate(
        groups[:limit],
        1
    ):

        title = (
            getattr(
                group,
                "title",
                None
            )
            or "Noma’lum"
        )

        username = getattr(
            group,
            "username",
            None
        )

        username_text = (
            f"@{username}"
            if username
            else "Username yo‘q"
        )

        group_id = getattr(
            group,
            "id",
            "?"
        )

        text += (
            f"{i}. <b>{title}</b>\n"
            f"   👤 {username_text}\n"
            f"   🆔 <code>{group_id}</code>\n\n"
        )

    return text


# =========================================================
# 4. CHAT / XABAR QIDIRISH
# =========================================================

async def search_chats(client, query, limit=100):

    query = clean_query(query)

    if not query:
        return []

    chats = []

    try:

        response = await client(
            SearchGlobalRequest(
                q=query,
                filter=None,
                min_date=None,
                max_date=None,
                offset_id=0,
                offset_rate=0,
                max_id=0,
                min_id=0,
                limit=limit
            )
        )

        for chat in response.chats:

            if isinstance(
                chat,
                (Channel, Chat)
            ):

                chats.append(chat)

    except Exception as e:

        print(
            "CHAT SEARCH ERROR:",
            repr(e)
        )

    return unique_by_id(chats)


# =========================================================
# 5. XABARLARNI QIDIRISH
# =========================================================

async def search_messages(
    client,
    query,
    limit=100
):

    query = clean_query(query)

    if not query:
        return []

    messages = []

    try:

        response = await client(
            SearchGlobalRequest(
                q=query,
                filter=None,
                min_date=None,
                max_date=None,
                offset_id=0,
                offset_rate=0,
                max_id=0,
                min_id=0,
                limit=limit
            )
        )

        for message in response.messages:

            if message is None:
                continue

            messages.append(message)

    except Exception as e:

        print(
            "MESSAGE SEARCH ERROR:",
            repr(e)
        )

    return messages


# =========================================================
# XABAR FORMAT
# =========================================================

def format_messages(messages, limit=30):

    if not messages:

        return (
            "💬 <b>CHAT / XABARLAR</b>\n\n"
            "❌ Mos public xabar topilmadi."
        )

    text = (
        "💬 <b>CHAT / XABARLAR</b>\n\n"
    )

    for i, message in enumerate(
        messages[:limit],
        1
    ):

        message_text = (
            getattr(
                message,
                "message",
                None
            )
            or "(matn yo‘q)"
        )

        message_text = str(
            message_text
        )

        # HTML xavfsizligi
        message_text = (
            message_text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        if len(message_text) > 250:

            message_text = (
                message_text[:250]
                + "..."
            )

        text += (
            f"{i}. {message_text}\n"
            f"🆔 Message ID: "
            f"<code>{getattr(message, 'id', '?')}</code>\n\n"
        )

    return text


# =========================================================
# 6. REAKSIYALAR
# =========================================================

def search_reactions(messages):

    reactions = []

    for message in messages:

        try:

            reaction_data = getattr(
                message,
                "reactions",
                None
            )

            if not reaction_data:
                continue

            reaction_results = getattr(
                reaction_data,
                "results",
                []
            )

            for reaction in reaction_results:

                reactions.append(
                    {
                        "message_id":
                            getattr(
                                message,
                                "id",
                                None
                            ),

                        "reaction":
                            reaction
                    }
                )

        except Exception as e:

            print(
                "REACTION ERROR:",
                repr(e)
            )

    return reactions


# =========================================================
# REAKSIYALAR FORMAT
# =========================================================

def format_reactions(
    reactions,
    limit=50
):

    if not reactions:

        return (
            "❤️ <b>REAKSIYALAR</b>\n\n"
            "❌ Topilgan xabarlarda "
            "reaksiya ma’lumoti yo‘q."
        )

    text = (
        "❤️ <b>REAKSIYALAR</b>\n\n"
    )

    for i, item in enumerate(
        reactions[:limit],
        1
    ):

        reaction = item.get(
            "reaction"
        )

        count = getattr(
            reaction,
            "count",
            0
        )

        reaction_obj = getattr(
            reaction,
            "reaction",
            None
        )

        reaction_name = (
            str(reaction_obj)
            if reaction_obj
            else "❤️"
        )

        text += (
            f"{i}. {reaction_name}\n"
            f"   🔢 Soni: <b>{count}</b>\n"
            f"   🆔 Xabar: "
            f"<code>{item.get('message_id')}</code>\n\n"
        )

    return text


# =========================================================
# TO‘LIQ MA'LUMOT
# =========================================================

def format_summary(user):

    if not isinstance(
        user,
        User
    ):

        return (
            "❌ Foydalanuvchi topilmadi."
        )

    first_name = (
        user.first_name or ""
    )

    last_name = (
        user.last_name or ""
    )

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    username = (
        f"@{user.username}"
        if user.username
        else "Username yo‘q"
    )

    return (
        "📊 <b>TO‘LIQ MA'LUMOT</b>\n\n"

        f"📝 Ism: "
        f"<b>{full_name or 'Noma’lum'}</b>\n"

        f"👤 Username: "
        f"<b>{username}</b>\n"

        f"🆔 ID: "
        f"<code>{user.id}</code>\n\n"

        f"☑️ Tasdiqlangan: "
        f"<b>{'Ha' if getattr(user, 'verified', False) else 'Yo‘q'}</b>\n"

        f"⭐ Premium: "
        f"<b>{'Ha' if getattr(user, 'premium', False) else 'Yo‘q'}</b>\n"

        f"🤖 Bot: "
        f"<b>{'Ha' if getattr(user, 'bot', False) else 'Yo‘q'}</b>"
    )
