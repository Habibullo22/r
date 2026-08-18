from telethon.tl.types import User, Channel, Chat
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.messages import SearchGlobalRequest


# =========================================================
# USERNAME TOZALASH
# =========================================================

def clean_username(value):
    value = (value or "").strip()

    if value.startswith("@"):
        value = value[1:]

    return value


# =========================================================
# PROFIL QIDIRISH
# =========================================================

async def find_user(client, query):

    query = (query or "").strip()

    if not query:
        return None

    try:

        # Telegram ID
        if query.isdigit():

            try:
                return await client.get_entity(
                    int(query)
                )
            except Exception:
                pass

        # Username
        username = clean_username(query)

        if username:

            try:
                return await client.get_entity(
                    username
                )
            except Exception:
                pass

        # Public Telegram qidiruvi
        try:

            result = await client(
                SearchRequest(
                    q=query,
                    limit=20
                )
            )

            for user in result.users:

                if isinstance(user, User):

                    # Username mosligi
                    if (
                        user.username
                        and user.username.lower()
                        == username.lower()
                    ):
                        return user

                    # Ism bo‘yicha moslik
                    full_name = (
                        f"{user.first_name or ''} "
                        f"{user.last_name or ''}"
                    ).strip().lower()

                    if query.lower() in full_name:
                        return user

        except Exception as e:

            print(
                "PUBLIC USER SEARCH ERROR:",
                repr(e)
            )

    except Exception as e:

        print(
            "FIND USER ERROR:",
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
        "✅ Tasdiqlangan"
        if getattr(user, "verified", False)
        else "—"
    )

    return (
        "👤 <b>PROFIL</b>\n\n"
        f"📝 Ism: <b>{full_name or 'Noma’lum'}</b>\n"
        f"👤 Username: <b>{username}</b>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"☑️ Status: <b>{verified}</b>"
    )


# =========================================================
# GLOBAL PUBLIC QIDIRUV
# =========================================================

async def global_search(client, query, limit=100):

    results = {
        "users": [],
        "channels": [],
        "groups": [],
        "messages": [],
        "reactions": []
    }

    query = (query or "").strip()

    if not query:
        return results

    try:

        # =================================================
        # TELEGRAM GLOBAL MESSAGE SEARCH
        # =================================================

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

        # =================================================
        # USERS / CHATS
        # =================================================

        for user in response.users:

            if isinstance(user, User):

                results["users"].append(user)

        for chat in response.chats:

            if isinstance(chat, Channel):

                # Megagroup = guruh
                if getattr(
                    chat,
                    "megagroup",
                    False
                ):

                    results["groups"].append(chat)

                else:

                    results["channels"].append(chat)

            elif isinstance(chat, Chat):

                results["groups"].append(chat)

        # =================================================
        # XABARLAR
        # =================================================

        for message in response.messages:

            if message is not None:

                results["messages"].append(
                    message
                )

    except Exception as e:

        print(
            "GLOBAL SEARCH ERROR:",
            repr(e)
        )

    # =====================================================
    # DUPLIKATLARNI OLIB TASHLASH
    # =====================================================

    results["users"] = unique_entities(
        results["users"]
    )

    results["channels"] = unique_entities(
        results["channels"]
    )

    results["groups"] = unique_entities(
        results["groups"]
    )

    return results


# =========================================================
# UNIQUE
# =========================================================

def unique_entities(items):

    result = []
    seen = set()

    for item in items:

        item_id = getattr(
            item,
            "id",
            None
        )

        if item_id is None:
            continue

        if item_id in seen:
            continue

        seen.add(item_id)

        result.append(item)

    return result


# =========================================================
# KANALLAR FORMAT
# =========================================================

def format_channels(channels, limit=50):

    text = "📢 <b>KANALLAR</b>\n\n"

    if not channels:

        return (
            text +
            "❌ Public kanal topilmadi."
        )

    for i, channel in enumerate(
        channels[:limit],
        1
    ):

        username = getattr(
            channel,
            "username",
            None
        )

        if username:

            username_text = (
                f"@{username}"
            )

        else:

            username_text = (
                "Username yo‘q"
            )

        title = getattr(
            channel,
            "title",
            "Noma’lum"
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

    text = "👥 <b>GURUHLAR</b>\n\n"

    if not groups:

        return (
            text +
            "❌ Public guruh topilmadi."
        )

    for i, group in enumerate(
        groups[:limit],
        1
    ):

        username = getattr(
            group,
            "username",
            None
        )

        if username:

            username_text = (
                f"@{username}"
            )

        else:

            username_text = (
                "Username yo‘q"
            )

        title = getattr(
            group,
            "title",
            "Noma’lum"
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

    text = "💬 <b>XABARLAR</b>\n\n"

    if not messages:

        return (
            text +
            "❌ Public xabar topilmadi."
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

        message_text = (
            message_text
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

async def search_reactions(
    client,
    messages
):

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

            results = getattr(
                reaction_data,
                "results",
                []
            )

            for reaction in results:

                reactions.append({
                    "message_id":
                        getattr(
                            message,
                            "id",
                            None
                        ),

                    "reaction":
                        reaction
                })

        except Exception as e:

            print(
                "REACTION ERROR:",
                repr(e)
            )

    return reactions


# =========================================================
# REAKSIYA FORMAT
# =========================================================

def format_reactions(
    reactions,
    limit=50
):

    text = "❤️ <b>REAKSIYALAR</b>\n\n"

    if not reactions:

        return (
            text +
            "❌ Reaksiya ma’lumotlari topilmadi."
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

        text += (
            f"{i}. ❤️ "
            f"Reaksiyalar: <b>{count}</b>\n"
        )

    return text


# =========================================================
# UMUMIY NATIJA
# =========================================================

def format_summary(results):

    users = len(
        results.get(
            "users",
            []
        )
    )

    channels = len(
        results.get(
            "channels",
            []
        )
    )

    groups = len(
        results.get(
            "groups",
            []
        )
    )

    messages = len(
        results.get(
            "messages",
            []
        )
    )

    reactions = len(
        results.get(
            "reactions",
            []
        )
    )

    return (
        "📊 <b>UMUMIY NATIJA</b>\n\n"
        f"👤 Profillar: <b>{users}</b>\n"
        f"📢 Kanallar: <b>{channels}</b>\n"
        f"👥 Guruhlar: <b>{groups}</b>\n"
        f"💬 Xabarlar: <b>{messages}</b>\n"
        f"❤️ Reaksiyalar: <b>{reactions}</b>\n\n"
        "🌐 Qidiruv public Telegram "
        "manbalaridagi natijalarga asoslangan."
    )
