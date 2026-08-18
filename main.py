import telebot
from telebot import types

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER,
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

from telegram_client import create_client

from search import (
    find_user,
    format_user,
    search_user_messages,
    search_user_chats,
)


# =========================================================
# TEKSHIRUV
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID topilmadi!")


# =========================================================
# BOT
# =========================================================

bot = telebot.TeleBot(BOT_TOKEN)


# =========================================================
# TELEGRAM ACCOUNT
# =========================================================

telegram_client = create_client()


# =========================================================
# HOLATLAR
# =========================================================

waiting_receipt = {}
waiting_search = set()


# =========================================================
# ASOSIY MENYU
# =========================================================

def main_menu(user_id=None):

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton(
            "🔎 Foydalanuvchi qidirish",
            callback_data="search_user"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "👥 Guruhlar",
            callback_data="groups"
        ),
        types.InlineKeyboardButton(
            "📢 Kanallar",
            callback_data="channels"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "💬 Qayerda yozgan",
            callback_data="messages"
        ),
        types.InlineKeyboardButton(
            "❤️ Reaksiyalar",
            callback_data="reactions"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "📊 To‘liq ma’lumot",
            callback_data="full_info"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "💳 Tariflar",
            callback_data="tariffs"
        )
    )

    # Faqat ADMIN uchun
    if user_id == ADMIN_ID:

        markup.add(
            types.InlineKeyboardButton(
                "👑 ADMIN PANEL",
                callback_data="admin_panel"
            )
        )

    return markup


# =========================================================
# TARIF MENYUSI
# =========================================================

def tariffs_menu():

    markup = types.InlineKeyboardMarkup(row_width=1)

    tariffs = get_tariffs()

    if tariffs:

        for tariff in tariffs:

            tariff_id = tariff[0]
            name = tariff[1]
            price = tariff[2]
            days = tariff[3]

            button_text = (
                f"{name} — {price:,} so‘m / {days} kun"
            ).replace(",", " ")

            markup.add(
                types.InlineKeyboardButton(
                    button_text,
                    callback_data=f"tariff_{tariff_id}"
                )
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
# ADMIN MENYU
# =========================================================

def admin_menu():

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton(
            "💳 Tariflar",
            callback_data="admin_tariffs"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "📱 Akkaunt holati",
            callback_data="admin_account"
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
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    try:

        save_user(
            message.from_user
        )

        bot.send_message(
            message.chat.id,

            "👋 <b>Assalomu alaykum!</b>\n\n"
            "🔎 <b>Telegram Search Bot</b>ga xush kelibsiz.\n\n"
            "Kerakli bo‘limni tanlang:",

            parse_mode="HTML",

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
# ADMIN CALLBACK
#
# MUHIM:
# BU HANDLER UMUMIY CALLBACKDAN OLDIN TURIBDI
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("approve_")
        or call.data.startswith("reject_")
)
def admin_payment_callback(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    try:

        # =====================================================
        # TASDIQLASH
        # =====================================================

        if call.data.startswith("approve_"):

            purchase_id = int(
                call.data.split("_")[1]
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

            approve_purchase(
                purchase_id
            )

            user_id = purchase[1]

            try:
                tariff_name = purchase[7]
            except Exception:
                tariff_name = "Tarif"

            try:
                days = purchase[9]
            except Exception:
                days = 0

            bot.send_message(
                user_id,

                "🎉 <b>TO‘LOV TASDIQLANDI!</b>\n\n"
                f"📦 Tarif: <b>{tariff_name}</b>\n"
                f"⏳ Muddat: <b>{days} kun</b>\n\n"
                "🔎 Qidiruv funksiyasi ochildi.",

                parse_mode="HTML",

                reply_markup=main_menu(
                    user_id
                )
            )

            try:

                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None
                )

            except Exception:
                pass

            bot.answer_callback_query(
                call.id,
                "✅ To‘lov tasdiqlandi!"
            )

            print(
                f"PAYMENT APPROVED: {purchase_id}"
            )

            return

        # =====================================================
        # RAD ETISH
        # =====================================================

        if call.data.startswith("reject_"):

            purchase_id = int(
                call.data.split("_")[1]
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

            reject_purchase(
                purchase_id
            )

            user_id = purchase[1]

            bot.send_message(
                user_id,

                "❌ <b>TO‘LOV RAD ETILDI</b>\n\n"
                "To‘lov arizangiz admin tomonidan "
                "rad etildi.\n\n"
                "Qayta urinib ko‘rishingiz mumkin.",

                parse_mode="HTML",

                reply_markup=main_menu(
                    user_id
                )
            )

            try:

                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None
                )

            except Exception:
                pass

            bot.answer_callback_query(
                call.id,
                "❌ Ariza rad etildi."
            )

            print(
                f"PAYMENT REJECTED: {purchase_id}"
            )

            return

    except Exception as e:

        print(
            "ADMIN PAYMENT ERROR:",
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
# BOSHQA CALLBACKLAR
# =========================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callbacks(call):

    user_id = call.from_user.id

    try:

        # =====================================================
        # NO ACTION
        # =====================================================

        if call.data == "no_action":

            bot.answer_callback_query(
                call.id
            )

            return

        # =====================================================
        # ADMIN PANEL
        # =====================================================

        if call.data == "admin_panel":

            bot.answer_callback_query(
                call.id
            )

            if user_id != ADMIN_ID:

                bot.send_message(
                    call.message.chat.id,
                    "⛔ Sizda admin huquqi yo‘q."
                )

                return

            bot.send_message(
                call.message.chat.id,

                "👑 <b>ADMIN PANEL</b>\n\n"
                "Kerakli bo‘limni tanlang:",

                parse_mode="HTML",

                reply_markup=admin_menu()
            )

            return

        # =====================================================
        # ADMIN ACCOUNT
        # =====================================================

        if call.data == "admin_account":

            bot.answer_callback_query(
                call.id
            )

            if user_id != ADMIN_ID:
                return

            try:

                if not telegram_client.is_connected():

                    telegram_client.connect()

                me = telegram_client.loop.run_until_complete(
                    telegram_client.get_me()
                )

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
                    "🟢 Holat: <b>Ulangan</b>",

                    parse_mode="HTML",

                    reply_markup=admin_menu()
                )

            except Exception as e:

                print(
                    "ACCOUNT ERROR:",
                    repr(e)
                )

                bot.send_message(
                    call.message.chat.id,

                    "🔴 <b>Telegram akkaunt ulanmagan.</b>\n\n"
                    f"<code>{str(e)[:500]}</code>",

                    parse_mode="HTML",

                    reply_markup=admin_menu()
                )

            return

        # =====================================================
        # ADMIN TARIFLAR
        # =====================================================

        if call.data == "admin_tariffs":

            bot.answer_callback_query(
                call.id
            )

            if user_id != ADMIN_ID:
                return

            bot.send_message(
                call.message.chat.id,

                "💳 <b>TARIFLAR</b>\n\n"
                "Hozirgi tariflar:",

                parse_mode="HTML",

                reply_markup=tariffs_menu()
            )

            return

        # =====================================================
        # TARIFLAR
        # =====================================================

        if call.data == "tariffs":

            bot.answer_callback_query(
                call.id
            )

            bot.edit_message_text(
                "💳 <b>TARIFLAR</b>\n\n"
                "O‘zingizga mos tarifni tanlang:",

                call.message.chat.id,
                call.message.message_id,

                parse_mode="HTML",

                reply_markup=tariffs_menu()
            )

            return

        # =====================================================
        # TARIF TANLASH
        # =====================================================

        if call.data.startswith("tariff_"):

            bot.answer_callback_query(
                call.id
            )

            tariff_id = int(
                call.data.split("_")[1]
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

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "💳 Sotib olish",
                    callback_data=f"buy_{tariff_id}"
                )
            )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Tariflar",
                    callback_data="tariffs"
                )
            )

            text = (
                f"💳 <b>{name}</b>\n\n"
                f"💰 Narxi: <b>{price:,} so‘m</b>\n"
                f"⏳ Muddat: <b>{days} kun</b>\n\n"
                "Sotib olish uchun tugmani bosing."
            ).replace(",", " ")

            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=markup
            )

            return

        # =====================================================
        # SOTIB OLISH
        # =====================================================

        if call.data.startswith("buy_"):

            bot.answer_callback_query(
                call.id
            )

            if has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,

                    "⚠️ Sizda hozir aktiv tarif mavjud.\n\n"
                    "Avval mavjud tarifingiz tugashini kuting.",

                    parse_mode="HTML"
                )

                return

            tariff_id = int(
                call.data.split("_")[1]
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
                "To‘lovni amalga oshirgandan keyin "
                "«✅ To‘lov qildim» tugmasini bosing."
            ).replace(",", " ")

            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=markup
            )

            return

        # =====================================================
        # CHEK YUBORISH
        # =====================================================

        if call.data.startswith("receipt_"):

            bot.answer_callback_query(
                call.id
            )

            purchase_id = int(
                call.data.split("_")[1]
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

                "📸 <b>TO‘LOV CHEKINI YUBORING</b>\n\n"
                "Chekni rasm ko‘rinishida yuboring.\n\n"
                "Admin tekshirganidan keyin "
                "tarif aktiv qilinadi.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # QIDIRUV
        # =====================================================

        if call.data == "search_user":

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,

                    "🔒 <b>QIDIRUV YOPIQ</b>\n\n"
                    "Qidiruvdan foydalanish uchun "
                    "avval tarif sotib oling.",

                    parse_mode="HTML",

                    reply_markup=tariffs_menu()
                )

                return

            waiting_search.add(
                user_id
            )

            bot.send_message(
                call.message.chat.id,

                "🔎 <b>FOYDALANUVCHI QIDIRISH</b>\n\n"
                "Username yoki Telegram ID yuboring.\n\n"
                "Masalan:\n"
                "<code>@username</code>\n"
                "yoki\n"
                "<code>123456789</code>\n\n"
                "Bekor qilish: /cancel",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # GURUHLAR
        # =====================================================

        if call.data == "groups":

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Avval tarif sotib oling.",
                    reply_markup=tariffs_menu()
                )

                return

            waiting_search.add(
                user_id
            )

            bot.send_message(
                call.message.chat.id,

                "👥 <b>GURUHLARNI QIDIRISH</b>\n\n"
                "Username yoki Telegram ID yuboring.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # KANALLAR
        # =====================================================

        if call.data == "channels":

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Avval tarif sotib oling.",
                    reply_markup=tariffs_menu()
                )

                return

            waiting_search.add(
                user_id
            )

            bot.send_message(
                call.message.chat.id,

                "📢 <b>KANALLARNI QIDIRISH</b>\n\n"
                "Username yoki Telegram ID yuboring.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # XABARLAR
        # =====================================================

        if call.data == "messages":

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Avval tarif sotib oling.",
                    reply_markup=tariffs_menu()
                )

                return

            waiting_search.add(
                user_id
            )

            bot.send_message(
                call.message.chat.id,

                "💬 <b>QAYERDA YOZGANINI QIDIRISH</b>\n\n"
                "Username yoki Telegram ID yuboring.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # REAKSIYALAR
        # =====================================================

        if call.data == "reactions":

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Avval tarif sotib oling.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,

                "❤️ <b>REAKSIYALAR</b>\n\n"
                "Telegram API orqali mavjud bo‘lgan "
                "reaksiya ma’lumotlari tekshiriladi.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # TO‘LIQ MA'LUMOT
        # =====================================================

        if call.data == "full_info":

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Avval tarif sotib oling.",
                    reply_markup=tariffs_menu()
                )

                return

            waiting_search.add(
                user_id
            )

            bot.send_message(
                call.message.chat.id,

                "📊 <b>TO‘LIQ QIDIRUV</b>\n\n"
                "Username yoki Telegram ID yuboring.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # ORQAGA
        # =====================================================

        if call.data == "back_main":

            bot.answer_callback_query(
                call.id
            )

            bot.edit_message_text(
                "🏠 <b>ASOSIY MENYU</b>\n\n"
                "Kerakli bo‘limni tanlang:",

                call.message.chat.id,
                call.message.message_id,

                parse_mode="HTML",

                reply_markup=main_menu(
                    user_id
                )
            )

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
# QIDIRUV
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.from_user.id in waiting_search
)
def search_message(message):

    user_id = message.from_user.id

    query = (
        message.text or ""
    ).strip()

    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    if query == "/cancel":

        waiting_search.discard(
            user_id
        )

        bot.send_message(
            message.chat.id,
            "❌ Qidiruv bekor qilindi.",
            reply_markup=main_menu(
                user_id
            )
        )

        return

    # -----------------------------------------------------
    # TARIF
    # -----------------------------------------------------

    if not has_active_tariff(user_id):

        waiting_search.discard(
            user_id
        )

        bot.send_message(
            message.chat.id,

            "🔒 Aktiv tarif kerak.",

            reply_markup=tariffs_menu()
        )

        return

    # -----------------------------------------------------
    # QIDIRUV BOSHLANDI
    # -----------------------------------------------------

    bot.send_message(
        message.chat.id,

        "🔎 <b>QIDIRILMOQDA...</b>\n\n"
        "⏳ Telegram akkauntidagi mavjud "
        "ma’lumotlar tekshirilmoqda.",

        parse_mode="HTML"
    )

    try:

        # Telegram account ulanishi
        if not telegram_client.is_connected():

            telegram_client.connect()

        # -------------------------------------------------
        # USERNI TOPISH
        # -------------------------------------------------

        user = telegram_client.loop.run_until_complete(
            find_user(
                telegram_client,
                query
            )
        )

        if not user:

            waiting_search.discard(
                user_id
            )

            bot.send_message(
                message.chat.id,

                "❌ <b>FOYDALANUVCHI TOPILMADI</b>\n\n"
                "Username yoki IDni tekshirib qayta "
                "urinib ko‘ring.",

                parse_mode="HTML",

                reply_markup=main_menu(
                    user_id
                )
            )

            return

        # -------------------------------------------------
        # PROFIL
        # -------------------------------------------------

        profile = format_user(
            user
        )

        bot.send_message(
            message.chat.id,
            profile,
            parse_mode="HTML"
        )

        # -------------------------------------------------
        # CHATLAR
        # -------------------------------------------------

        chats = telegram_client.loop.run_until_complete(
            search_user_chats(
                telegram_client,
                user
            )
        )

        # -------------------------------------------------
        # XABARLAR
        # -------------------------------------------------

        messages = telegram_client.loop.run_until_complete(
            search_user_messages(
                telegram_client,
                user
            )
        )

        # -------------------------------------------------
        # GURUHLAR
        # -------------------------------------------------

        groups = [
            item
            for item in chats
            if item.get("type") == "group"
        ]

        if groups:

            text = (
                "👥 <b>GURUHLAR</b>\n\n"
            )

            for index, item in enumerate(
                groups[:50],
                1
            ):

                text += (
                    f"{index}. "
                    f"{item.get('title', 'Noma’lum')}\n"
                )

            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML"
            )

        else:

            bot.send_message(
                message.chat.id,

                "👥 <b>GURUHLAR</b>\n\n"
                "Mavjud ma’lumot topilmadi.",

                parse_mode="HTML"
            )

        # -------------------------------------------------
        # KANALLAR
        # -------------------------------------------------

        channels = [
            item
            for item in chats
            if item.get("type") == "channel"
        ]

        if channels:

            text = (
                "📢 <b>KANALLAR</b>\n\n"
            )

            for index, item in enumerate(
                channels[:50],
                1
            ):

                text += (
                    f"{index}. "
                    f"{item.get('title', 'Noma’lum')}\n"
                )

            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML"
            )

        else:

            bot.send_message(
                message.chat.id,

                "📢 <b>KANALLAR</b>\n\n"
                "Mavjud ma’lumot topilmadi.",

                parse_mode="HTML"
            )

        # -------------------------------------------------
        # QAYERDA YOZGAN
        # -------------------------------------------------

        if messages:

            text = (
                "💬 <b>QAYERDA YOZGAN</b>\n\n"
            )

            total = 0

            for item in messages[:50]:

                count = len(
                    item.get(
                        "messages",
                        []
                    )
                )

                total += count

                text += (
                    f"📍 <b>"
                    f"{item.get('title', 'Noma’lum')}"
                    f"</b>\n"
                    f"   💬 Xabarlar: <b>{count}</b>\n\n"
                )

            text += (
                f"📊 Jami topilgan xabarlar: "
                f"<b>{total}</b>"
            )

            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML"
            )

        else:

            bot.send_message(
                message.chat.id,

                "💬 <b>QAYERDA YOZGAN</b>\n\n"
                "Mavjud xabar topilmadi.",

                parse_mode="HTML"
            )

        # -------------------------------------------------
        # YAKUN
        # -------------------------------------------------

        waiting_search.discard(
            user_id
        )

        bot.send_message(
            message.chat.id,

            "📊 <b>QIDIRUV YAKUNLANDI</b>\n\n"
            "Natijalar Telegram API orqali "
            "akkaunt ko‘ra oladigan ma’lumotlar "
            "asosida chiqarildi.",

            parse_mode="HTML",

            reply_markup=main_menu(
                user_id
            )
        )

    except Exception as e:

        print(
            "SEARCH ERROR:",
            repr(e)
        )

        waiting_search.discard(
            user_id
        )

        bot.send_message(
            message.chat.id,

            "❌ <b>QIDIRUVDA XATOLIK</b>\n\n"
            f"<code>{str(e)[:700]}</code>",

            parse_mode="HTML",

            reply_markup=main_menu(
                user_id
            )
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
            "ℹ️ Hozir sizdan chek kutilmayapti.",
            reply_markup=main_menu(
                user_id
            )
        )

        return

    purchase_id = waiting_receipt[
        user_id
    ]

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

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "✅ Tasdiqlash",
            callback_data=f"approve_{purchase_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Rad etish",
            callback_data=f"reject_{purchase_id}"
        )
    )

    username = message.from_user.username

    if username:

        username_text = (
            f"@{username}"
        )

    else:

        username_text = (
            "Username yo‘q"
        )

    try:

        tariff_name = purchase[7]

    except Exception:

        tariff_name = "Noma’lum"

    try:

        price = purchase[8]

    except Exception:

        price = 0

    admin_text = (
        "💳 <b>YANGI TO‘LOV</b>\n\n"
        f"🧾 Ariza: <code>#{purchase_id}</code>\n"
        f"👤 Foydalanuvchi: {username_text}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📦 Tarif: <b>{tariff_name}</b>\n"
        f"💰 Summa: <b>{price:,} so‘m</b>"
    ).replace(",", " ")

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,

        caption=admin_text,

        parse_mode="HTML",

        reply_markup=markup
    )

    bot.send_message(
        message.chat.id,

        "✅ <b>CHEK QABUL QILINDI</b>\n\n"
        "Chekingiz adminga yuborildi.\n"
        "⏳ Tasdiqlanishini kuting.",

        parse_mode="HTML"
    )

    waiting_receipt.pop(
        user_id,
        None
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
            "MESSAGE ERROR:",
            repr(e)
        )


# =========================================================
# ISHGA TUSHIRISH
# =========================================================

if __name__ == "__main__":

    print(
        "================================"
    )

    print(
        "🗄️ DATABASE ISHGA TUSHMOQDA"
    )

    print(
        "================================"
    )

    init_database()

    print(
        "🤖 TELEGRAM SEARCH BOT"
    )

    print(
        "================================"
    )

    print(
        "✅ BOT ISHGA TUSHDI"
    )

    print(
        "================================"
    )

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
