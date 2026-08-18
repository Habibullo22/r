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

if not API_ID:
    raise RuntimeError("API_ID topilmadi!")

if not API_HASH:
    raise RuntimeError("API_HASH topilmadi!")


# =========================================================
# BOT
# =========================================================

bot = telebot.TeleBot(
    BOT_TOKEN
)


# =========================================================
# TELEGRAM USER ACCOUNT
# =========================================================

telegram_client = create_client()


# =========================================================
# HOLATLAR
# =========================================================

waiting_search = set()

waiting_receipt = {}


# =========================================================
# ASOSIY MENU
# =========================================================

def main_menu(user_id=None):

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

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

    # FAQAT ADMIN
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

    markup = types.InlineKeyboardMarkup(
        row_width=1
    )

    tariffs = get_tariffs()

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
                    "TARIFF ERROR:",
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

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

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
# START
# =========================================================

@bot.message_handler(
    commands=["start"]
)
def start(message):

    try:

        save_user(
            message.from_user
        )

        bot.send_message(
            message.chat.id,

            "👋 <b>Assalomu alaykum!</b>\n\n"
            "🔎 <b>Telegram Search Bot</b>\n\n"
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
# ADMIN TO‘LOV CALLBACK
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

        user_id = purchase[1]

        # =====================================================
        # APPROVE
        # =====================================================

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

            print(
                f"PAYMENT APPROVED: {purchase_id}"
            )

            return

        # =====================================================
        # REJECT
        # =====================================================

        if call.data.startswith("reject_"):

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

            print(
                f"PAYMENT REJECTED: {purchase_id}"
            )

            return

    except Exception as e:

        print(
            "PAYMENT CALLBACK ERROR:",
            repr(e)
        )

        bot.answer_callback_query(
            call.id,
            "❌ Xatolik!",
            show_alert=True
        )


# =========================================================
# UMUMIY CALLBACK
# =========================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callbacks(call):

    user_id = call.from_user.id

    try:

        # =====================================================
        # ADMIN PANEL
        # =====================================================

        if call.data == "admin_panel":

            bot.answer_callback_query(
                call.id
            )

            if user_id != ADMIN_ID:

                return

            bot.edit_message_text(
                "👑 <b>ADMIN PANEL</b>\n\n"
                "Kerakli bo‘limni tanlang:",

                call.message.chat.id,
                call.message.message_id,

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

                # Client main()da allaqachon start qilingan
                me = telegram_client.get_me()

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

                    parse_mode="HTML",

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
                    f"<code>{str(e)[:500]}</code>",

                    parse_mode="HTML"
                )

            return

        # =====================================================
        # ADMIN TARIF
        # =====================================================

        if call.data == "admin_tariffs":

            bot.answer_callback_query(
                call.id
            )

            if user_id != ADMIN_ID:

                return

            bot.send_message(
                call.message.chat.id,

                "💳 <b>TARIFLAR</b>",

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
                "Kerakli tarifni tanlang:",

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
                parse_mode="HTML",
                reply_markup=markup
            )

            return

        # =====================================================
        # BUY
        # =====================================================

        if call.data.startswith("buy_"):

            bot.answer_callback_query(
                call.id
            )

            if has_active_tariff(
                user_id
            ):

                bot.send_message(
                    call.message.chat.id,

                    "⚠️ Sizda aktiv tarif mavjud.",

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
                "To‘lovdan keyin tugmani bosing."
            ).replace(",", " ")

            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=markup
            )

            return

        # =====================================================
        # RECEIPT
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

                "📸 <b>CHEKNI YUBORING</b>\n\n"
                "To‘lov chekini rasm qilib yuboring.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # SEARCH
        # =====================================================

        if call.data in (
            "search_user",
            "groups",
            "channels",
            "messages",
            "full_info"
        ):

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(
                user_id
            ):

                bot.send_message(
                    call.message.chat.id,

                    "🔒 <b>QIDIRUV YOPIQ</b>\n\n"
                    "Avval tarif sotib oling.",

                    parse_mode="HTML",

                    reply_markup=tariffs_menu()
                )

                return

            waiting_search.add(
                user_id
            )

            bot.send_message(
                call.message.chat.id,

                "🔎 <b>QIDIRUV</b>\n\n"
                "Username yoki Telegram ID yuboring.\n\n"
                "Masalan:\n"
                "<code>@username</code>\n"
                "<code>123456789</code>\n\n"
                "/cancel — bekor qilish",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # REACTIONS
        # =====================================================

        if call.data == "reactions":

            bot.answer_callback_query(
                call.id
            )

            if not has_active_tariff(
                user_id
            ):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Avval tarif sotib oling.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,

                "❤️ <b>REAKSIYALAR</b>\n\n"
                "Faqat Telegram API orqali "
                "olinadigan mavjud reaksiya "
                "ma’lumotlari ko‘rsatiladi.",

                parse_mode="HTML"
            )

            return

        # =====================================================
        # BACK
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

        # =====================================================
        # NO ACTION
        # =====================================================

        if call.data == "no_action":

            bot.answer_callback_query(
                call.id
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
# SEARCH MESSAGE
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

    # CANCEL
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

    # TARIF
    if not has_active_tariff(
        user_id
    ):

        waiting_search.discard(
            user_id
        )

        bot.send_message(
            message.chat.id,

            "🔒 Aktiv tarif kerak.",

            reply_markup=tariffs_menu()
        )

        return

    bot.send_message(
        message.chat.id,

        "🔎 <b>QIDIRILMOQDA...</b>\n\n"
        "⏳ Ma’lumotlar tekshirilmoqda.",

        parse_mode="HTML"
    )

    try:

        # MUHIM:
        # Bu yerda connect() YO‘Q.
        # Client main()da start() qilingan.

        if not telegram_client.is_connected():

            raise RuntimeError(
                "Telegram akkaunt ulanmagan."
            )

        # USER
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

                "❌ <b>FOYDALANUVCHI TOPILMADI</b>",

                parse_mode="HTML",

                reply_markup=main_menu(
                    user_id
                )
            )

            return

        # PROFIL
        bot.send_message(
            message.chat.id,

            format_user(
                user
            ),

            parse_mode="HTML"
        )

        # CHATLAR
        chats = telegram_client.loop.run_until_complete(
            search_user_chats(
                telegram_client,
                user
            )
        )

        # XABARLAR
        messages = telegram_client.loop.run_until_complete(
            search_user_messages(
                telegram_client,
                user
            )
        )

        # GURUHLAR
        groups = [
            item
            for item in chats
            if item.get("type") == "group"
        ]

        text = "👥 <b>GURUHLAR</b>\n\n"

        if groups:

            for index, item in enumerate(
                groups[:50],
                1
            ):

                text += (
                    f"{index}. "
                    f"{item.get('title', 'Noma’lum')}\n"
                )

        else:

            text += (
                "Mavjud ma’lumot topilmadi."
            )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML"
        )

        # KANALLAR
        channels = [
            item
            for item in chats
            if item.get("type") == "channel"
        ]

        text = "📢 <b>KANALLAR</b>\n\n"

        if channels:

            for index, item in enumerate(
                channels[:50],
                1
            ):

                text += (
                    f"{index}. "
                    f"{item.get('title', 'Noma’lum')}\n"
                )

        else:

            text += (
                "Mavjud ma’lumot topilmadi."
            )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML"
        )

        # XABARLAR
        text = "💬 <b>QAYERDA YOZGAN</b>\n\n"

        total = 0

        if messages:

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
                    f"💬 Xabarlar: <b>{count}</b>\n\n"
                )

            text += (
                f"📊 Jami: <b>{total}</b>"
            )

        else:

            text += (
                "Mavjud xabar topilmadi."
            )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML"
        )

        waiting_search.discard(
            user_id
        )

        bot.send_message(
            message.chat.id,

            "✅ <b>QIDIRUV YAKUNLANDI</b>",

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

            "❌ <b>QIDIRUVDA XATO</b>\n\n"
            f"<code>{str(e)[:700]}</code>",

            parse_mode="HTML",

            reply_markup=main_menu(
                user_id
            )
        )


# =========================================================
# CHEK
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

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "Username yo‘q"
    )

    text = (
        "💳 <b>YANGI TO‘LOV ARIZASI</b>\n\n"
        f"🧾 Ariza: <code>#{purchase_id}</code>\n"
        f"👤 User: {username}\n"
        f"🆔 ID: <code>{user_id}</code>"
    )

    markup = types.InlineKeyboardMarkup()

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

    bot.send_photo(
        ADMIN_ID,

        message.photo[-1].file_id,

        caption=text,

        parse_mode="HTML",

        reply_markup=markup
    )

    bot.send_message(
        message.chat.id,

        "✅ <b>CHEK ADMINGA YUBORILDI</b>\n\n"
        "⏳ Admin tasdiqlashini kuting.",

        parse_mode="HTML"
    )

    waiting_receipt.pop(
        user_id,
        None
    )


# =========================================================
# BOSHQA XABAR
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

        telegram_client.start()

me = telegram_client.loop.run_until_complete(
    telegram_client.get_me()
)

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
