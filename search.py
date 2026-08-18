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
# USER TOPISH
# =========================================================

async def find_user(client, query):

    query = (query or "").strip()

    if not query:
        return None

    # =====================================================
    # ID ORQALI
    # =====================================================

    if query.isdigit():

        try:
            entity = await client.get_entity(
                int(query)
            )

            if isinstance(entity, User):
                return entity

        except Exception as e:

            print(
                "ID SEARCH ERROR:",
                repr(e)
            )

    # =====================================================
    # USERNAME ORQALI
    # =====================================================

    username = clean_username(query)

    if username:

        try:

            entity = await client.get_entity(
                username
            )

            if isinstance(entity, User):
                return entity

        except Exception as e:

            print(
                "USERNAME SEARCH ERROR:",
                repr(e)
            )

    # =====================================================
    # PUBLIC TELEGRAM SEARCH
    # =====================================================

    try:

        result = await client(
            SearchRequest(
                q=query,
                limit=50
            )
        )

        for user in result.users:

            if not isinstance(user, User):
                continue

            # Username mosligi

            if user.username:

                if (
                    user.username.lower()
                    == username.lower()
                ):
                    return user

            # Ism mosligi

            full_name = (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip().lower()

            if (
                query.lower()
                in full_name
            ):
                return user

    except Exception as e:

        print(
            "PUBLIC USER SEARCH ERROR:",
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

    first_name = (
        user.first_name
        or ""
    )

    last_name = (
        user.last_name
        or ""
    )

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
        if getattr(
            user,
            "verified",
            False
        )
        else "—"
    )

    return (
        "👤 <b>PROFIL</b>\n\n"
        f"📝 Ism: "
        f"<b>{full_name or 'Noma’lum'}</b>\n"
        f"👤 Username: "
        f"<b>{username}</b>\n"
        f"🆔 ID: "
        f"<code>{user.id}</code>\n"
        f"☑️ Status: "
        f"<b>{verified}</b>"
    )


# =========================================================
# GLOBAL PUBLIC QIDIRUV
# =========================================================

async def global_search(
    client,
    query,
    limit=100
):

    results = {
        "users": [],
        "channels": [],
        "groups": [],
        "messages": [],
        "reactions": []
    }

    query = (
        query or ""
    ).strip()

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
        # USERS
        # =================================================

        for user in response.users:

            if isinstance(
                user,
                User
            ):

                results["users"].append(
                    user
                )

        # =================================================
        # CHANNELS / GROUPS
        # =================================================

        for chat in response.chats:

            if isinstance(
                chat,
                Channel
            ):

                # Supergroup
                if getattr(
                    chat,
                    "megagroup",
                    False
                ):

                    results[
                        "groups"
                    ].append(chat)

                # Channel
                else:

                    results[
                        "channels"
                    ].append(chat)

            elif isinstance(
                chat,
                Chat
            ):

                results[
                    "groups"
                ].append(chat)

        # =================================================
        # MESSAGES
        # =================================================

        for message in response.messages:

            if message is not None:

                results[
                    "messages"
                ].append(message)

    except Exception as e:

        print(
            "GLOBAL SEARCH ERROR:",
            repr(e)
        )

    # =====================================================
    # DUPLIKATLAR
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

    # =====================================================
    # REAKSIYALAR
    # =====================================================

    results["reactions"] = search_reactions(
        results["messages"]
    )

    return results


# =========================================================
# UNIQUE ENTITIES
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

        result.append(
            item
        )

    return result


# =========================================================
# KANALLAR
# =========================================================

def format_channels(
    channels,
    limit=50
):

    text = ""

    if not channels:

        return (
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

        username_text = (
            f"@{username}"
            if username
            else "Username yo‘q"
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
# GURUHLAR
# =========================================================

def format_groups(
    groups,
    limit=50
):

    text = ""

    if not groups:

        return (
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

        username_text = (
            f"@{username}"
            if username
            else "Username yo‘q"
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
# XABARLAR
# =========================================================

def format_messages(
    messages,
    limit=30
):

    text = ""

    if not messages:

        return (
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
            str(message_text)
            .replace(
                "<",
                "&lt;"
            )
            .replace(
                ">",
                "&gt;"
            )
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

def search_reactions(
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

    text = ""

    if not reactions:

        return (
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
            f"Reaksiyalar: "
            f"<b>{count}</b>\n"
        )

    return text


# =========================================================
# UMUMIY NATIJA
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

    users_count = len(
        results.get(
            "users",
            []
        )
    )

    channels_count = len(
        results.get(
            "channels",
            []
        )
    )

    groups_count = len(
        results.get(
            "groups",
            []
        )
    )

    messages_count = len(
        results.get(
            "messages",
            []
        )
    )

    reactions_count = len(
        reactions
    )

    username = (
        f"@{user.username}"
        if getattr(
            user,
            "username",
            None
        )
        else "Username yo‘q"
    )

    return (
        f"👤 Profil: "
        f"<b>{username}</b>\n"
        f"🆔 ID: "
        f"<code>{user.id}</code>\n\n"

        f"👤 Qo‘shimcha profillar: "
        f"<b>{users_count}</b>\n"
        f"📢 Kanallar: "
        f"<b>{channels_count}</b>\n"
        f"👥 Guruhlar: "
        f"<b>{groups_count}</b>\n"
        f"💬 Xabarlar: "
        f"<b>{messages_count}</b>\n"
        f"❤️ Reaksiyalar: "
        f"<b>{reactions_count}</b>\n\n"

        "🌐 Natijalar Telegram'ning "
        "public qidiruv imkoniyatlari "
        "orqali olindi."
    )
