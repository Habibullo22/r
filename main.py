import telebot
from telebot import types

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER,
    API_ID,
    API_HASH,
)

from database import (
    init_database,
    save_user,
    get_tariffs,
    get_tariff,
    create_purchase,
    get_purchase,
    approve_purchase,
    reject_purchase,
    has_active_tariff,
)

from telegram_client import (
    telegram_client,
    start_client,
    get_me,
    run_async,
)

from search import (
    find_user,
    format_user,
    search_channels,
    format_channels,
    search_groups,
    format_groups,
    search_chats,
    search_messages,
    format_messages,
    search_reactions,
    format_reactions,
    format_summary,
)


# =========================================================
# TEKSHIRUV
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID topilmadi!")

if not API_ID:
    raise RuntimeError("API_ID topilmadi!")

if not API_HASH:
    raise RuntimeError("API_HASH topilmadi!")


# =========================================================
# BOT
# =========================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML",
    threaded=False
)


# =========================================================
# HOLATLAR
# =========================================================

# Foydalanuvchi qaysi qidiruv turini tanlagan
search_mode = {}

# To'lov cheki kutilayotgan userlar
waiting_receipt = {}


# =========================================================
# PROGRESS
# =========================================================

def progress_bar(percent):
    percent = max(0, min(100, int(percent)))

    blocks = round(percent / 10)

    return (
        "█" * blocks +
        "░" * (10 - blocks)
    )


def progress_text(title, percent, detail=""):
    return (
        f"🔎 <b>{title}</b>\n\n"
        f"[{progress_bar(percent)}] {percent}%\n"
        f"{detail}"
    )


def safe_edit(chat_id, message_id, text, markup=None):
    try:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception as e:
        print("EDIT ERROR:", repr(e))


# =========================================================
# ASOSIY MENU
# =========================================================

def main_menu(user_id=None):

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton(
            "🔎 Foydalanuvchi",
            callback_data="search_profile"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "👥 Guruhlar",
            callback_data="search_groups"
        ),
        types.InlineKeyboardButton(
            "📢 Kanallar",
            callback_data="search_channels"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "💬 Qayerda yozgan",
            callback_data="search_messages"
        ),
        types.InlineKeyboardButton(
            "❤️ Reaksiyalar",
            callback_data="search_reactions"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "📊 To‘liq ma’lumot",
            callback_data="search_full"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "💳 Tariflar",
            callback_data="tariffs"
        )
    )

    if user_id == ADMIN_ID:
        markup.add(
            types.InlineKeyboardButton(
                "👑 ADMIN PANEL",
                callback_data="admin_panel"
            )
        )

    return markup


# =========================================================
# TARIF MENU
# =========================================================

def tariffs_menu():

    markup = types.InlineKeyboardMarkup(row_width=1)

    try:
        tariffs = get_tariffs()
    except Exception as e:
        print("GET TARIFFS ERROR:", repr(e))
        tariffs = []

    if tariffs:

        for tariff in tariffs:

            try:
                tariff_id = tariff[0]
                name = tariff[1]
                price = tariff[2]
                days = tariff[3]

                text = (
                    f"{name} — "
                    f"{price:,} so‘m / "
                    f"{days} kun"
                ).replace(",", " ")

                markup.add(
                    types.InlineKeyboardButton(
                        text,
                        callback_data=f"tariff_{tariff_id}"
                    )
                )

            except Exception as e:
                print(
                    "TARIFF BUTTON ERROR:",
                    repr(e)
                )

    else:

        markup.add(
            types.InlineKeyboardButton(
                "❌ Tariflar mavjud emas",
                callback_data="no_action"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="back_main"
        )
    )

    return markup


# =========================================================
# ADMIN MENU
# =========================================================

def admin_menu():

    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "📱 Akkaunt holati",
            callback_data="admin_account"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "💳 Tariflar",
            callback_data="admin_tariffs"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "⬅️ Asosiy menyu",
            callback_data="back_main"
        )
    )

    return markup


# =========================================================
# SEARCH MODE MENU
# =========================================================

def search_mode_name(mode):

    names = {
        "profile": "👤 Foydalanuvchi",
        "channels": "📢 Kanallar",
        "groups": "👥 Guruhlar",
        "messages": "💬 Qayerda yozgan",
        "reactions": "❤️ Reaksiyalar",
        "full": "📊 To‘liq ma’lumot",
    }

    return names.get(mode, "🔎 Qidiruv")


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    try:
        save_user(message.from_user)

        bot.send_message(
            message.chat.id,
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "🔎 <b>Telegram Search Bot</b>\n\n"
            "Kerakli bo‘limni tanlang:",
            reply_markup=main_menu(
                message.from_user.id
            )
        )

    except Exception as e:

        print(
            "START ERROR:",
            repr(e)
        )

        bot.send_message(
            message.chat.id,
            "❌ Xatolik yuz berdi."
        )


# =========================================================
# CANCEL
# =========================================================

@bot.message_handler(commands=["cancel"])
def cancel(message):

    user_id = message.from_user.id

    search_mode.pop(
        user_id,
        None
    )

    waiting_receipt.pop(
        user_id,
        None
    )

    bot.send_message(
        message.chat.id,
        "❌ Amal bekor qilindi.",
        reply_markup=main_menu(user_id)
    )


# =========================================================
# TO'LOV APPROVE / REJECT
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("approve_")
        or call.data.startswith("reject_")
)
def payment_callback(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ Ruxsat yo‘q!",
            show_alert=True
        )

        return

    try:

        purchase_id = int(
            call.data.split("_", 1)[1]
        )

        purchase = get_purchase(
            purchase_id
        )

        if not purchase:

            bot.answer_callback_query(
                call.id,
                "❌ Ariza topilmadi.",
                show_alert=True
            )

            return

        user_id = purchase[1]

        # APPROVE
        if call.data.startswith("approve_"):

            approve_purchase(
                purchase_id
            )

            bot.answer_callback_query(
                call.id,
                "✅ Tasdiqlandi!"
            )

            bot.send_message(
                user_id,
                "🎉 <b>TO‘LOV TASDIQLANDI!</b>\n\n"
                "✅ Tarifingiz aktiv qilindi.\n"
                "🔎 Endi qidiruvdan foydalanishingiz mumkin.",
                reply_markup=main_menu(user_id)
            )

        # REJECT
        else:

            reject_purchase(
                purchase_id
            )

            bot.answer_callback_query(
                call.id,
                "❌ Rad etildi."
            )

            bot.send_message(
                user_id,
                "❌ <b>TO‘LOV RAD ETILDI</b>\n\n"
                "Admin to‘lovni tasdiqlamadi.",
                reply_markup=main_menu(user_id)
            )

        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass

    except Exception as e:

        print(
            "PAYMENT CALLBACK ERROR:",
            repr(e)
        )

        try:
            bot.answer_callback_query(
                call.id,
                "❌ Xatolik!",
                show_alert=True
            )
        except Exception:
            pass


# =========================================================
# CALLBACK
# =========================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callbacks(call):

    user_id = call.from_user.id

    try:

        # =================================================
        # ADMIN PANEL
        # =================================================

        if call.data == "admin_panel":

            bot.answer_callback_query(call.id)

            if user_id != ADMIN_ID:
                return

            bot.edit_message_text(
                "👑 <b>ADMIN PANEL</b>\n\n"
                "Kerakli bo‘limni tanlang:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=admin_menu()
            )

            return

        # =================================================
        # ADMIN ACCOUNT
        # =================================================

        if call.data == "admin_account":

            bot.answer_callback_query(call.id)

            if user_id != ADMIN_ID:
                return

            try:

                me = get_me()

                username = (
                    f"@{me.username}"
                    if me.username
                    else "Username yo‘q"
                )

                bot.send_message(
                    call.message.chat.id,
                    "📱 <b>TELEGRAM AKKAUNT</b>\n\n"
                    f"👤 Ism: <b>{me.first_name or ''}</b>\n"
                    f"👤 Username: <b>{username}</b>\n"
                    f"🆔 ID: <code>{me.id}</code>\n\n"
                    "🟢 Holat: <b>ULANGAN</b>",
                    reply_markup=admin_menu()
                )

            except Exception as e:

                print(
                    "ADMIN ACCOUNT ERROR:",
                    repr(e)
                )

                bot.send_message(
                    call.message.chat.id,
                    "🔴 <b>Akkaunt holatini olishda xato.</b>\n\n"
                    f"<code>{str(e)[:500]}</code>"
                )

            return

        # =================================================
        # ADMIN TARIFF
        # =================================================

        if call.data == "admin_tariffs":

            bot.answer_callback_query(call.id)

            if user_id != ADMIN_ID:
                return

            bot.send_message(
                call.message.chat.id,
                "💳 <b>TARIFLAR</b>",
                reply_markup=tariffs_menu()
            )

            return

        # =================================================
        # TARIFF
        # =================================================

        if call.data == "tariffs":

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
                "💳 <b>TARIFLAR</b>\n\n"
                "Kerakli tarifni tanlang:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=tariffs_menu()
            )

            return

        # =================================================
        # TARIFF TANLASH
        # =================================================

        if call.data.startswith("tariff_"):

            bot.answer_callback_query(call.id)

            tariff_id = int(
                call.data.split("_", 1)[1]
            )

            tariff = get_tariff(
                tariff_id
            )

            if not tariff:

                bot.send_message(
                    call.message.chat.id,
                    "❌ Tarif topilmadi."
                )

                return

            name = tariff[1]
            price = tariff[2]
            days = tariff[3]

            markup = types.InlineKeyboardMarkup(
                row_width=1
            )

            markup.add(
                types.InlineKeyboardButton(
                    "💳 Sotib olish",
                    callback_data=f"buy_{tariff_id}"
                )
            )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="tariffs"
                )
            )

            text = (
                "💳 <b>TARIF</b>\n\n"
                f"📦 {name}\n"
                f"💰 {price:,} so‘m\n"
                f"⏳ {days} kun\n\n"
                "Sotib olishni tasdiqlang."
            ).replace(",", " ")

            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=markup
            )

            return

        # =================================================
        # BUY
        # =================================================

        if call.data.startswith("buy_"):

            bot.answer_callback_query(call.id)

            if has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "⚠️ Sizda aktiv tarif mavjud."
                )

                return

            tariff_id = int(
                call.data.split("_", 1)[1]
            )

            tariff = get_tariff(
                tariff_id
            )

            if not tariff:

                bot.send_message(
                    call.message.chat.id,
                    "❌ Tarif topilmadi."
                )

                return

            name = tariff[1]
            price = tariff[2]
            days = tariff[3]

            purchase_id = create_purchase(
                user_id,
                tariff_id
            )

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "✅ To‘lov qildim",
                    callback_data=f"receipt_{purchase_id}"
                )
            )

            text = (
                "💳 <b>TO‘LOV</b>\n\n"
                f"📦 Tarif: <b>{name}</b>\n"
                f"💰 Summa: <b>{price:,} so‘m</b>\n"
                f"⏳ Muddat: <b>{days} kun</b>\n\n"
                f"💳 Karta:\n"
                f"<code>{CARD_NUMBER}</code>\n\n"
                f"👤 Karta egasi:\n"
                f"<b>{CARD_OWNER}</b>\n\n"
                f"🧾 Ariza: <code>#{purchase_id}</code>\n\n"
                "To‘lovdan keyin tugmani bosing."
            ).replace(",", " ")

            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=markup
            )

            return

        # =================================================
        # RECEIPT
        # =================================================

        if call.data.startswith("receipt_"):

            bot.answer_callback_query(call.id)

            purchase_id = int(
                call.data.split("_", 1)[1]
            )

            purchase = get_purchase(
                purchase_id
            )

            if not purchase:

                bot.send_message(
                    call.message.chat.id,
                    "❌ Ariza topilmadi."
                )

                return

            waiting_receipt[user_id] = purchase_id

            bot.send_message(
                call.message.chat.id,
                "📸 <b>CHEKNI YUBORING</b>\n\n"
                "To‘lov chekini rasm qilib yuboring."
            )

            return

        # =================================================
        # SEARCH MODE
        # =================================================

        modes = {
            "search_profile": "profile",
            "search_channels": "channels",
            "search_groups": "groups",
            "search_messages": "messages",
            "search_reactions": "reactions",
            "search_full": "full",
        }

        if call.data in modes:

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 <b>QIDIRUV YOPIQ</b>\n\n"
                    "Avval tarif sotib oling.",
                    reply_markup=tariffs_menu()
                )

                return

            mode = modes[call.data]

            search_mode[user_id] = mode

            bot.send_message(
                call.message.chat.id,

                f"{search_mode_name(mode)}\n\n"
                "🔎 Username yoki Telegram ID yuboring.\n\n"
                "Masalan:\n"
                "<code>@username</code>\n"
                "<code>123456789</code>\n\n"
                "/cancel — bekor qilish"
            )

            return

        # =================================================
        # BACK
        # =================================================

        if call.data == "back_main":

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
                "🏠 <b>ASOSIY MENYU</b>\n\n"
                "Kerakli bo‘limni tanlang:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=main_menu(user_id)
            )

            return

        # =================================================
        # NO ACTION
        # =================================================

        if call.data == "no_action":

            bot.answer_callback_query(call.id)
            return

    except Exception as e:

        print(
            "CALLBACK ERROR:",
            repr(e)
        )

        try:
            bot.answer_callback_query(
                call.id,
                "❌ Xatolik yuz berdi.",
                show_alert=True
            )
        except Exception:
            pass


# =========================================================
# QIDIRUV XABARI
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.from_user.id in search_mode
)
def search_message(message):

    user_id = message.from_user.id
    query = (message.text or "").strip()

    if query.lower() == "/cancel":

        search_mode.pop(
            user_id,
            None
        )

        bot.send_message(
            message.chat.id,
            "❌ Qidiruv bekor qilindi.",
            reply_markup=main_menu(user_id)
        )

        return

    if not query:

        bot.send_message(
            message.chat.id,
            "❌ Username yoki Telegram ID yuboring."
        )

        return

    if not has_active_tariff(user_id):

        search_mode.pop(
            user_id,
            None
        )

        bot.send_message(
            message.chat.id,
            "🔒 Aktiv tarif kerak.",
            reply_markup=tariffs_menu()
        )

        return

    mode = search_mode.get(
        user_id
    )

    if not mode:
        return

    # =====================================================
    # STATUS
    # =====================================================

    status = bot.send_message(
        message.chat.id,
        progress_text(
            search_mode_name(mode),
            0,
            "⏳ Qidiruv boshlanmoqda..."
        )
    )

    try:

        # =================================================
        # TELEGRAM ACCOUNT
        # =================================================

        if not telegram_client.is_connected():

            raise RuntimeError(
                "Telegram akkaunt ulanmagan."
            )

        # =================================================
        # PROFIL
        # =================================================

        safe_edit(
            message.chat.id,
            status.message_id,
            progress_text(
                search_mode_name(mode),
                15,
                "⏳ Foydalanuvchi qidirilmoqda..."
            )
        )

        user = run_async(
            find_user(
                telegram_client,
                query
            )
        )

        if not user:

            safe_edit(
                message.chat.id,
                status.message_id,
                "❌ <b>FOYDALANUVCHI TOPILMADI</b>"
            )

            return

        # =================================================
        # PROFILE
        # =================================================

        if mode == "profile":

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "👤 Foydalanuvchi",
                    100,
                    "✅ Profil topildi."
                )
            )

            bot.send_message(
                message.chat.id,
                format_user(user),
                reply_markup=main_menu(user_id)
            )

            return

        # =================================================
        # FULL INFO
        # =================================================

        if mode == "full":

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "📊 To‘liq ma’lumot",
                    100,
                    "✅ Profil ma’lumotlari tayyor."
                )
            )

            bot.send_message(
                message.chat.id,
                format_summary(user),
                reply_markup=main_menu(user_id)
            )

            return

        # =================================================
        # CHANNELS
        # =================================================

        if mode == "channels":

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "📢 Kanallar",
                    35,
                    "⏳ Kanallar qidirilmoqda..."
                )
            )

            channels = run_async(
                search_channels(
                    telegram_client,
                    query,
                    limit=100
                )
            )

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "📢 Kanallar",
                    100,
                    f"✅ Tekshiruv tugadi. Topilgan: {len(channels)}"
                )
            )

            bot.send_message(
                message.chat.id,
                format_channels(channels),
                reply_markup=main_menu(user_id)
            )

            return

        # =================================================
        # GROUPS
        # =================================================

        if mode == "groups":

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "👥 Guruhlar",
                    35,
                    "⏳ Guruhlar qidirilmoqda..."
                )
            )

            groups = run_async(
                search_groups(
                    telegram_client,
                    query,
                    limit=100
                )
            )

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "👥 Guruhlar",
                    100,
                    f"✅ Tekshiruv tugadi. Topilgan: {len(groups)}"
                )
            )

            bot.send_message(
                message.chat.id,
                format_groups(groups),
                reply_markup=main_menu(user_id)
            )

            return

        # =================================================
        # MESSAGES / CHAT
        # =================================================

        if mode == "messages":

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "💬 Qayerda yozgan",
                    35,
                    "⏳ Chatlar qidirilmoqda..."
                )
            )

            chats = run_async(
                search_chats(
                    telegram_client,
                    query,
                    limit=100
                )
            )

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "💬 Qayerda yozgan",
                    65,
                    f"📂 Chatlar topildi: {len(chats)}\n"
                    "⏳ Xabarlar qidirilmoqda..."
                )
            )

            messages = run_async(
                search_messages(
                    telegram_client,
                    query,
                    limit=100
                )
            )

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "💬 Qayerda yozgan",
                    100,
                    f"✅ Xabarlar: {len(messages)}"
                )
            )

            if chats:

                bot.send_message(
                    message.chat.id,
                    format_groups(
                        [
                            chat
                            for chat in chats
                            if (
                                getattr(
                                    chat,
                                    "megagroup",
                                    False
                                )
                                or isinstance(
                                    chat,
                                    __import__(
                                        "telethon.tl.types",
                                        fromlist=["Chat"]
                                    ).Chat
                                )
                            )
                        ]
                    )
                )

            bot.send_message(
                message.chat.id,
                format_messages(messages),
                reply_markup=main_menu(user_id)
            )

            return

        # =================================================
        # REACTIONS
        # =================================================

        if mode == "reactions":

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "❤️ Reaksiyalar",
                    35,
                    "⏳ Xabarlar qidirilmoqda..."
                )
            )

            messages = run_async(
                search_messages(
                    telegram_client,
                    query,
                    limit=100
                )
            )

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "❤️ Reaksiyalar",
                    70,
                    f"💬 Xabarlar: {len(messages)}\n"
                    "⏳ Reaksiyalar tekshirilmoqda..."
                )
            )

            reactions = search_reactions(
                messages
            )

            safe_edit(
                message.chat.id,
                status.message_id,
                progress_text(
                    "❤️ Reaksiyalar",
                    100,
                    f"✅ Reaksiyalar: {len(reactions)}"
                )
            )

            bot.send_message(
                message.chat.id,
                format_reactions(reactions),
                reply_markup=main_menu(user_id)
            )

            return

    except Exception as e:

        print(
            "SEARCH ERROR:",
            repr(e)
        )

        safe_edit(
            message.chat.id,
            status.message_id,
            "❌ <b>QIDIRUVDA XATO</b>\n\n"
            f"<code>{str(e)[:700]}</code>"
        )

    finally:

        search_mode.pop(
            user_id,
            None
        )


# =========================================================
# CHEK QABUL QILISH
# =========================================================

@bot.message_handler(
    content_types=["photo"]
)
def receive_receipt(message):

    user_id = message.from_user.id

    if user_id not in waiting_receipt:

        bot.send_message(
            message.chat.id,
            "ℹ️ Hozir chek kutilmayapti.",
            reply_markup=main_menu(user_id)
        )

        return

    purchase_id = waiting_receipt[user_id]

    purchase = get_purchase(
        purchase_id
    )

    if not purchase:

        waiting_receipt.pop(
            user_id,
            None
        )

        bot.send_message(
            message.chat.id,
            "❌ Ariza topilmadi."
        )

        return

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "Username yo‘q"
    )

    caption = (
        "💳 <b>YANGI TO‘LOV ARIZASI</b>\n\n"
        f"🧾 Ariza: <code>#{purchase_id}</code>\n"
        f"👤 User: {username}\n"
        f"🆔 ID: <code>{user_id}</code>"
    )

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

    markup.add(
        types.InlineKeyboardButton(
            "✅ TASDIQLASH",
            callback_data=f"approve_{purchase_id}"
        ),
        types.InlineKeyboardButton(
            "❌ RAD ETISH",
            callback_data=f"reject_{purchase_id}"
        )
    )

    try:

        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=caption,
            reply_markup=markup
        )

        bot.send_message(
            message.chat.id,
            "✅ <b>CHEK ADMINGA YUBORILDI</b>\n\n"
            "⏳ Admin tasdiqlashini kuting."
        )

        waiting_receipt.pop(
            user_id,
            None
        )

    except Exception as e:

        print(
            "RECEIPT ERROR:",
            repr(e)
        )

        bot.send_message(
            message.chat.id,
            "❌ Chekni yuborishda xatolik."
        )


# =========================================================
# BOSHQA XABARLAR
# =========================================================

@bot.message_handler(
    func=lambda message: True
)
def other_messages(message):

    try:

        save_user(
            message.from_user
        )

        bot.send_message(
            message.chat.id,
            "ℹ️ Menyudagi tugmalardan foydalaning.",
            reply_markup=main_menu(
                message.from_user.id
            )
        )

    except Exception as e:

        print(
            "OTHER MESSAGE ERROR:",
            repr(e)
        )


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":

    print("================================")
    print("🗄 DATABASE ISHGA TUSHMOQDA")
    print("================================")

    init_database()

    print("📱 TELEGRAM AKKAUNT ULANMOQDA...")
    print("================================")

    try:

        start_client()

        me = get_me()

        print("================================")
        print("✅ TELEGRAM AKKAUNT ULANDI")
        print("================================")

        print(
            f"👤 Ism: {me.first_name or ''}"
        )

        print(
            f"🆔 ID: {me.id}"
        )

        if me.username:
            print(
                f"👤 Username: @{me.username}"
            )

        print("================================")

    except Exception as e:

        print("================================")
        print("❌ TELEGRAM AKKAUNT ULANMADI")
        print(
            f"XATO: {e}"
        )
        print("================================")

        raise

    print("🤖 BOT ISHGA TUSHDI")
    print("================================")

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
