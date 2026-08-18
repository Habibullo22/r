# search.py

from telethon.tl.types import User, Channel, Chat
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.messages import SearchGlobalRequest


# =========================================================
# YORDAMCHI
# =========================================================

def clean_username(value):
    value = (value or "").strip()

    if value.startswith("@"):
        value = value[1:]

    return value.strip()


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
# USER QIDIRISH
# =========================================================

async def find_user(client, query):

    query = (query or "").strip()

    if not query:
        return None

    # -----------------------------------------------------
    # ID
    # -----------------------------------------------------

    if query.isdigit():

        try:
            entity = await client.get_entity(int(query))

            if isinstance(entity, User):
                return entity

        except Exception as e:
            print("USER ID SEARCH ERROR:", repr(e))

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
            print("USERNAME SEARCH ERROR:", repr(e))

    # -----------------------------------------------------
    # TELEGRAM CONTACT SEARCH
    # -----------------------------------------------------

    try:

        result = await client(
            SearchRequest(
                q=username or query,
                limit=50
            )
        )

        for user in result.users:

            if not isinstance(user, User):
                continue

            if user.username:

                if user.username.lower() == username.lower():
                    return user

            full_name = (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip().lower()

            if query.lower() in full_name:
                return user

    except Exception as e:
        print("PUBLIC USER SEARCH ERROR:", repr(e))

    return None


# =========================================================
# USER FORMAT
# =========================================================

def format_user(user):

    if not user:
        return "❌ <b>FOYDALANUVCHI TOPILMADI</b>"

    first_name = getattr(user, "first_name", None) or ""
    last_name = getattr(user, "last_name", None) or ""

    full_name = f"{first_name} {last_name}".strip()

    username = getattr(user, "username", None)

    username_text = (
        f"@{username}"
        if username
        else "Username yo‘q"
    )

    verified = (
        "✅ Tasdiqlangan"
        if getattr(user, "verified", False)
        else "—"
    )

    return (
        "👤 <b>PROFIL</b>\n\n"
        f"📝 Ism: <b>{full_name or 'Noma’lum'}</b>\n"
        f"👤 Username: <b>{username_text}</b>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"☑️ Status: <b>{verified}</b>"
    )


# =========================================================
# GLOBAL QIDIRUV
#
# FAQAT:
# public Telegram qidiruvi
#
# max_id/min_id YO‘Q
# =========================================================

async def global_search(client, query, limit=100):

    results = {
        "users": [],
        "channels": [],
        "groups": [],
        "chats": [],
        "messages": [],
        "reactions": []
    }

    query = (query or "").strip()

    if not query:
        return results

    try:

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

        # -------------------------------------------------
        # USERS
        # -------------------------------------------------

        for user in response.users:

            if isinstance(user, User):
                results["users"].append(user)

        # -------------------------------------------------
        # CHANNELS / GROUPS
        # -------------------------------------------------

        for chat in response.chats:

            if isinstance(chat, Channel):

                if getattr(chat, "megagroup", False):

                    results["groups"].append(chat)

                else:

                    results["channels"].append(chat)

            elif isinstance(chat, Chat):

                results["groups"].append(chat)

                results["chats"].append(chat)

        # -------------------------------------------------
        # MESSAGES
        # -------------------------------------------------

        for message in response.messages:

            if message is not None:
                results["messages"].append(message)

    except Exception as e:

        print(
            "GLOBAL SEARCH ERROR:",
            repr(e)
        )

    results["users"] = unique_by_id(
        results["users"]
    )

    results["channels"] = unique_by_id(
        results["channels"]
    )

    results["groups"] = unique_by_id(
        results["groups"]
    )

    results["chats"] = unique_by_id(
        results["chats"]
    )

    results["reactions"] = search_reactions(
        results["messages"]
    )

    return results


# =========================================================
# KANALLARNI ALOHIDA QIDIRISH
# =========================================================

async def search_channels(client, query, limit=100):

    channels = []

    query = (query or "").strip()

    if not query:
        return channels

    try:

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
# GURUHLARNI ALOHIDA QIDIRISH
# =========================================================

async def search_groups(client, query, limit=100):

    groups = []

    query = (query or "").strip()

    if not query:
        return groups

    try:

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

            if isinstance(chat, Channel):

                if getattr(chat, "megagroup", False):
                    groups.append(chat)

            elif isinstance(chat, Chat):

                groups.append(chat)

    except Exception as e:

        print(
            "GROUP SEARCH ERROR:",
            repr(e)
        )

    return unique_by_id(groups)


# =========================================================
# CHATLAR
# =========================================================

async def search_chats(client, query, limit=100):

    chats = []

    query = (query or "").strip()

    if not query:
        return chats

    try:

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

            if isinstance(chat, Chat):
                chats.append(chat)

            elif isinstance(chat, Channel):

                if getattr(chat, "megagroup", False):
                    chats.append(chat)

    except Exception as e:

        print(
            "CHAT SEARCH ERROR:",
            repr(e)
        )

    return unique_by_id(chats)


# =========================================================
# XABARLARNI QIDIRISH
# =========================================================

async def search_messages(client, query, limit=100):

    messages = []

    query = (query or "").strip()

    if not query:
        return messages

    try:

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

        for message in response.messages:

            if message is not None:
                messages.append(message)

    except Exception as e:

        print(
            "MESSAGE SEARCH ERROR:",
            repr(e)
        )

    return messages


# =========================================================
# KANALLAR FORMAT
# =========================================================

def format_channels(channels, limit=50):

    if not channels:

        return (
            "📢 <b>KANALLAR</b>\n\n"
            "❌ Mos public kanal topilmadi."
        )

    text = "📢 <b>KANALLAR</b>\n\n"

    for i, channel in enumerate(
        channels[:limit],
        1
    ):

        title = (
            getattr(channel, "title", None)
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
# GURUHLAR FORMAT
# =========================================================

def format_groups(groups, limit=50):

    if not groups:

        return (
            "👥 <b>GURUHLAR</b>\n\n"
            "❌ Mos public guruh topilmadi."
        )

    text = "👥 <b>GURUHLAR</b>\n\n"

    for i, group in enumerate(
        groups[:limit],
        1
    ):

        title = (
            getattr(group, "title", None)
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

        text += (
            f"{i}. <b>{title}</b>\n"
            f"   👤 {username_text}\n"
            f"   🆔 <code>{group.id}</code>\n\n"
        )

    return text


# =========================================================
# XABARLAR FORMAT
# =========================================================

def format_messages(messages, limit=30):

    if not messages:

        return (
            "💬 <b>XABARLAR</b>\n\n"
            "❌ Mos public xabar topilmadi."
        )

    text = "💬 <b>XABARLAR</b>\n\n"

    for i, message in enumerate(
        messages[:limit],
        1
    ):

        message_text = (
            getattr(message, "message", None)
            or "(matn yo‘q)"
        )

        message_text = str(
            message_text
        )

        message_text = (
            message_text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        if len(message_text) > 300:

            message_text = (
                message_text[:300]
                + "..."
            )

        text += (
            f"{i}. {message_text}\n\n"
        )

    return text


# =========================================================
# REAKSIYALAR
# =========================================================

def search_reactions(messages):

    reactions = []

    if not messages:
        return reactions

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
                None
            )

            if not reaction_results:
                continue

            for reaction in reaction_results:

                reactions.append(
                    {
                        "message_id": getattr(
                            message,
                            "id",
                            None
                        ),

                        "reaction": reaction
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
            "❌ Reaksiya ma’lumotlari topilmadi."
        )

    text = "❤️ <b>REAKSIYALAR</b>\n\n"

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

        reaction_type = getattr(
            reaction,
            "reaction",
            None
        )

        emoji = "❤️"

        if reaction_type:

            emoji = getattr(
                reaction_type,
                "emoticon",
                None
            ) or "❤️"

        text += (
            f"{i}. {emoji} "
            f"<b>{count}</b> ta\n"
        )

    return text


# =========================================================
# TO‘LIQ NATIJA
# =========================================================

def format_summary(
    user,
    results,
    reactions=None
):

    if reactions is None:

        reactions = results.get(
            "reactions",
            []
        )

    username = getattr(
        user,
        "username",
        None
    )

    username_text = (
        f"@{username}"
        if username
        else "Username yo‘q"
    )

    return (
        "📊 <b>QIDIRUV NATIJASI</b>\n\n"

        f"👤 Profil: "
        f"<b>{username_text}</b>\n"

        f"🆔 ID: "
        f"<code>{getattr(user, 'id', '—')}</code>\n\n"

        f"👤 Profillar: "
        f"<b>{len(results.get('users', []))}</b>\n"

        f"📢 Kanallar: "
        f"<b>{len(results.get('channels', []))}</b>\n"

        f"👥 Guruhlar: "
        f"<b>{len(results.get('groups', []))}</b>\n"

        f"💬 Xabarlar: "
        f"<b>{len(results.get('messages', []))}</b>\n"

        f"❤️ Reaksiyalar: "
        f"<b>{len(reactions)}</b>\n\n"

        "🌐 Natijalar akkaunt ko‘ra oladigan "
        "public Telegram manbalaridan olindi."
    )
