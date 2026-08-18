import asyncio
from telegram_client import create_client
from search import find_user, format_user
import telebot
from telebot import types

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER
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


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)


# =========================
# VAQTINCHA CHEK SAQLASH
# =========================

waiting_receipt = {}


# =========================
# ASOSIY MENYU
# =========================

def main_menu():
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

    return markup


# =========================
# TARIFLAR
# =========================

def tariffs_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)

    tariffs = get_tariffs()

    for tariff in tariffs:
        tariff_id, name, price, days = tariff

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

    markup.add(
        types.InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="back_main"
        )
    )

    return markup


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    save_user(message.from_user)

    bot.send_message(
        message.chat.id,
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "🔎 Telegram Search Bot'ga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================
# CALLBACK
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    user_id = call.from_user.id

    try:

        # =====================
        # TARIFLAR
        # =====================

        if call.data == "tariffs":

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
                "💳 <b>Tariflar</b>\n\n"
                "O‘zingizga mos tarifni tanlang:",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=tariffs_menu()
            )

        # =====================
        # TARIF TANLASH
        # =====================

        elif call.data.startswith("tariff_"):

            bot.answer_callback_query(call.id)

            tariff_id = int(
                call.data.split("_")[1]
            )

            tariff = get_tariff(tariff_id)

            if not tariff:
                bot.send_message(
                    call.message.chat.id,
                    "❌ Tarif topilmadi."
                )
                return

            tariff_id, name, price, days = tariff

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

            bot.send_message(
                call.message.chat.id,
                f"💳 <b>{name}</b>\n\n"
                f"💰 Narxi: <b>{price:,} so‘m</b>\n"
                f"⏳ Muddati: <b>{days} kun</b>\n\n"
                "Sotib olish uchun tugmani bosing.",
                parse_mode="HTML",
                reply_markup=markup
            )

        # =====================
        # SOTIB OLISH
        # =====================

        elif call.data.startswith("buy_"):

            bot.answer_callback_query(call.id)

            tariff_id = int(
                call.data.split("_")[1]
            )

            tariff = get_tariff(tariff_id)

            if not tariff:
                bot.send_message(
                    call.message.chat.id,
                    "❌ Tarif topilmadi."
                )
                return

            tariff_id, name, price, days = tariff

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

            bot.send_message(
                call.message.chat.id,
                "💳 <b>To‘lov</b>\n\n"
                f"📦 Tarif: <b>{name}</b>\n"
                f"💰 Summa: <b>{price:,} so‘m</b>\n"
                f"⏳ Muddat: <b>{days} kun</b>\n\n"
                f"💳 Karta:\n"
                f"<code>{CARD_NUMBER}</code>\n\n"
                f"👤 Karta egasi:\n"
                f"<b>{CARD_OWNER}</b>\n\n"
                f"🧾 Ariza: <code>#{purchase_id}</code>\n\n"
                "To‘lovni amalga oshirgandan keyin "
                "«To‘lov qildim» tugmasini bosing.",
                parse_mode="HTML",
                reply_markup=markup
            )

        # =====================
        # CHEK YUBORISH
        # =====================

        elif call.data.startswith("receipt_"):

            bot.answer_callback_query(call.id)

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
                "📸 <b>To‘lov chekini yuboring.</b>\n\n"
                "Chekni rasm ko‘rinishida yuboring.\n\n"
                "Admin tekshirganidan keyin "
                "tarifingiz aktiv qilinadi.",
                parse_mode="HTML"
            )

        # =====================
        # QIDIRUV
        # =====================

        elif call.data == "search_user":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Qidiruvdan foydalanish uchun "
                    "aktiv tarif kerak.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,
                "🔎 Username yoki Telegram ID yuboring."
            )

        # =====================
        # GURUHLAR
        # =====================

        elif call.data == "groups":

            bot.answer_callback_query(call.id)
            if not has_active_tariff(user_id):
                bot.send_message(
                    call.message.chat.id,
                    "🔒 Aktiv tarif kerak.",
                    reply_markup=tariffs_menu()
                )
                return

            bot.send_message(
                call.message.chat.id,
                "👥 Guruhlar bo‘limi "
                "keyingi bosqichda qidiruv moduliga ulanadi."
            )

        # =====================
        # KANALLAR
        # =====================

        elif call.data == "channels":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):
                bot.send_message(
                    call.message.chat.id,
                    "🔒 Aktiv tarif kerak.",
                    reply_markup=tariffs_menu()
                )
                return

            bot.send_message(
                call.message.chat.id,
                "📢 Kanallar bo‘limi "
                "keyingi bosqichda ulanadi."
            )

        # =====================
        # XABARLAR
        # =====================

        elif call.data == "messages":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):
                bot.send_message(
                    call.message.chat.id,
                    "🔒 Aktiv tarif kerak.",
                    reply_markup=tariffs_menu()
                )
                return

            bot.send_message(
                call.message.chat.id,
                "💬 Qayerda yozgan bo‘limi "
                "keyingi bosqichda ulanadi."
            )

        # =====================
        # REAKSIYALAR
        # =====================

        elif call.data == "reactions":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):
                bot.send_message(
                    call.message.chat.id,
                    "🔒 Aktiv tarif kerak.",
                    reply_markup=tariffs_menu()
                )
                return

            bot.send_message(
                call.message.chat.id,
                "❤️ Reaksiyalar bo‘limi "
                "keyingi bosqichda ulanadi."
            )

        # =====================
        # TO‘LIQ MA'LUMOT
        # =====================

        elif call.data == "full_info":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):
                bot.send_message(
                    call.message.chat.id,
                    "🔒 Aktiv tarif kerak.",
                    reply_markup=tariffs_menu()
                )
                return

            bot.send_message(
                call.message.chat.id,
                "📊 To‘liq ma’lumot bo‘limi "
                "qidiruv moduli tayyor bo‘lgach ishlaydi."
            )

        # =====================
        # ORQAGA
        # =====================

        elif call.data == "back_main":

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
                "🏠 <b>Asosiy menyu</b>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=main_menu()
            )

    except Exception as e:

        print("CALLBACK ERROR:", e)

        try:
            bot.answer_callback_query(
                call.id,
                "❌ Xatolik yuz berdi.",
                show_alert=True
            )
        except Exception:
            pass


# =========================
# CHEK QABUL QILISH
# =========================

@bot.message_handler(content_types=["photo"])
def receive_receipt(message):

    user_id = message.from_user.id

    if user_id not in waiting_receipt:

        bot.send_message(
            message.chat.id,
            "ℹ️ Hozir sizdan chek kutilmayapti."
        )

        return

    purchase_id = waiting_receipt[user_id]

    purchase = get_purchase(
        purchase_id
    )

    if not purchase:

        del waiting_receipt[user_id]
        bot.send_message(
            message.chat.id,
            "❌ Ariza topilmadi."
        )

        return

    # Admin uchun tugmalar
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
        username_text = f"@{username}"
    else:
        username_text = "Username yo‘q"

    admin_text = (
        "💳 <b>YANGI TO‘LOV</b>\n\n"
        f"🧾 Ariza: <code>#{purchase_id}</code>\n"
        f"👤 Foydalanuvchi: {username_text}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📦 Tarif: <b>{purchase[7]}</b>\n"
        f"💰 Summa: <b>{purchase[8]:,} so‘m</b>\n"
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
        "✅ Chekingiz adminga yuborildi.\n\n"
        "⏳ Tasdiqlanishini kuting."
    )

    del waiting_receipt[user_id]


# =========================
# ADMIN TASDIQLASH / RAD ETISH
# =========================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("approve_")
        or call.data.startswith("reject_")
)
def admin_payment_callback(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ Siz admin emassiz.",
            show_alert=True
        )

        return

    try:

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
                    "Ariza topilmadi.",
                    show_alert=True
                )

                return

            if purchase[3] == "approved":

                bot.answer_callback_query(
                    call.id,
                    "Bu ariza allaqachon tasdiqlangan.",
                    show_alert=True
                )

                return

            approve_purchase(
                purchase_id
            )

            user_id = purchase[1]

            bot.send_message(
                user_id,
                "🎉 <b>To‘lov tasdiqlandi!</b>\n\n"
                f"📦 Tarif: <b>{purchase[7]}</b>\n"
                f"⏳ Muddat: <b>{purchase[9]} kun</b>\n\n"
                "🔎 Qidiruv funksiyasi ochildi.",
                parse_mode="HTML",
                reply_markup=main_menu()
            )

            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )

            bot.answer_callback_query(
                call.id,
                "✅ To‘lov tasdiqlandi!"
            )

        elif call.data.startswith("reject_"):

            purchase_id = int(
                call.data.split("_")[1]
            )

            purchase = get_purchase(
                purchase_id
            )

            if not purchase:

                bot.answer_callback_query(
                    call.id,
                    "Ariza topilmadi.",
                    show_alert=True
                )

                return

            reject_purchase(
                purchase_id
            )

            user_id = purchase[1]

            bot.send_message(
                user_id,
                "❌ <b>To‘lov arizangiz rad etildi.</b>\n\n"
                "Agar xato bo‘lgan deb hisoblasangiz, "
                "admin bilan bog‘laning.",
                parse_mode="HTML"
            )
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )

            bot.answer_callback_query(
                call.id,
                "❌ Ariza rad etildi."
            )

    except Exception as e:

        print("ADMIN PAYMENT ERROR:", e)

        bot.answer_callback_query(
            call.id,
            "❌ Xatolik yuz berdi.",
            show_alert=True
        )


# =========================
# BOSHQA XABARLAR
# =========================

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    save_user(message.from_user)

    bot.send_message(
        message.chat.id,
        "ℹ️ Menyudan foydalaning.",
        reply_markup=main_menu()
    )

# =========================
# START BOT
# =========================

if name == "main":

    init_database()

    print("================================")
    print("🤖 TELEGRAM SEARCH BOT")
    print("================================")
    print("✅ Bot ishga tushdi!")

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
