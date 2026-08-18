import telebot
from telebot import types

from config import BOT_TOKEN, ADMIN_ID

from database import (
    init_database,
    save_user,
    get_tariffs,
    get_tariff,
    create_purchase,
    has_active_tariff,
)


# =========================
# BOT
# =========================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)


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
# TARIFLAR MENYUSI
# =========================

def tariffs_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)

    tariffs = get_tariffs()

    for tariff in tariffs:
        tariff_id, name, price, days = tariff

        markup.add(
            types.InlineKeyboardButton(
                f"{name} — {price:,} so‘m / {days} kun".replace(",", " "),
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

    try:
        save_user(message.from_user)

        bot.send_message(
            message.chat.id,
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "🔎 <b>Telegram Search Bot</b>ga xush kelibsiz.\n\n"
            "Kerakli bo‘limni tanlang:",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

    except Exception as e:
        print("START ERROR:", e)

        bot.send_message(
            message.chat.id,
            "❌ Xatolik yuz berdi."
        )


# =========================
# CALLBACKLAR
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    try:

        user_id = call.from_user.id

        # -------------------------
        # QIDIRUV
        # -------------------------

        if call.data == "search_user":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 <b>Qidiruv yopiq.</b>\n\n"
                    "Qidiruvdan foydalanish uchun avval tarif sotib oling.",
                    parse_mode="HTML",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,
                "🔎 <b>Foydalanuvchi qidirish</b>\n\n"
                "Username yoki Telegram ID yuboring.\n\n"
                "Masalan:\n"
                "<code>@username</code>\n"
                "yoki\n"
                "<code>123456789</code>",
                parse_mode="HTML"
            )

        # -------------------------
        # GURUHLAR
        # -------------------------

        elif call.data == "groups":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):
                bot.send_message(
                    call.message.chat.id,
                    "🔒 Bu bo‘limdan foydalanish uchun tarif kerak.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,
                "👥 <b>Guruhlar</b>\n\n"
                "Bu bo‘lim real Telegram qidiruv moduliga ulanadi.",
                parse_mode="HTML"
            )

        # -------------------------
        # KANALLAR
        # -------------------------

        elif call.data == "channels":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Bu bo‘limdan foydalanish uchun tarif kerak.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,
                "📢 <b>Kanallar</b>\n\n"
                "Bu bo‘lim real Telegram qidiruv moduliga ulanadi.",
                parse_mode="HTML"
            )

        # -------------------------
        # XABARLAR
        # -------------------------

        elif call.data == "messages":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Bu bo‘limdan foydalanish uchun tarif kerak.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,
                "💬 <b>Qayerda yozgan</b>\n\n"
                "Bu bo‘lim real Telegram qidiruv moduliga ulanadi.",
                parse_mode="HTML"
            )

        # -------------------------
        # REAKSIYALAR
        # -------------------------

        elif call.data == "reactions":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Bu bo‘limdan foydalanish uchun tarif kerak.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,
                "❤️ <b>Reaksiyalar</b>\n\n"
                "Mavjud Telegram ma’lumotlari doirasida "
                "reaksiyalar tekshiriladi.",
                parse_mode="HTML"
            )

        # -------------------------
        # TO‘LIQ MA’LUMOT
        # -------------------------

        elif call.data == "full_info":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🔒 Bu bo‘limdan foydalanish uchun tarif kerak.",
                    reply_markup=tariffs_menu()
                )

                return

            bot.send_message(
                call.message.chat.id,
                "📊 <b>To‘liq ma’lumot</b>\n\n"
                "Barcha mavjud qidiruv natijalari "
                "keyingi bosqichda birlashtiriladi.",
                parse_mode="HTML"
            )

        # -------------------------
        # TARIFLAR
        # -------------------------

        elif call.data == "tariffs":

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
                "💳 <b>Tariflar</b>\n\n"
                "O‘zingizga mos tarifni tanlang:",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=tariffs_menu()
            )

        # -------------------------
        # TARIF TANLASH
        # -------------------------

        elif call.data.startswith("tariff_"):

            bot.answer_callback_query(call.id)

            tariff_id = int(call.data.split("_")[1])

            tariff = get_tariff(tariff_id)
            if not tariff:

                bot.send_message(
                    call.message.chat.id,
                    "❌ Tarif topilmadi."
                )

                return

            tariff_id, name, price, days = tariff

            text = (
                f"💳 <b>{name}</b>\n\n"
                f"💰 Narxi: <b>{price:,} so‘m</b>\n"
                f"⏳ Muddati: <b>{days} kun</b>\n\n"
                "Tarifni sotib olish uchun quyidagi tugmani bosing."
            ).replace(",", " ")

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "✅ Sotib olish",
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
                text,
                parse_mode="HTML",
                reply_markup=markup
            )

        # -------------------------
        # SOTIB OLISH
        # -------------------------

        elif call.data.startswith("buy_"):

            bot.answer_callback_query(call.id)

            tariff_id = int(call.data.split("_")[1])

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

            bot.send_message(
                call.message.chat.id,
                "💳 <b>To‘lov</b>\n\n"
                f"📦 Tarif: <b>{name}</b>\n"
                f"💰 Narxi: <b>{price:,} so‘m</b>\n"
                f"⏳ Muddati: <b>{days} kun</b>\n\n"
                "💳 Karta rekvizitlari keyingi bosqichda "
                "admin sozlamasidan olinadi.\n\n"
                f"🧾 Ariza raqami: <code>#{purchase_id}</code>\n\n"
                "To‘lovni amalga oshirgandan keyin "
                "to‘lov tasdig‘i tizimini ishlatamiz.",
                parse_mode="HTML"
            )

        # -------------------------
        # ORQAGA
        # -------------------------

        elif call.data == "back_main":

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
                "🏠 <b>Asosiy menyu</b>\n\n"
                "Kerakli bo‘limni tanlang:",
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
        except:
            pass


# =========================
# BOSHQA XABARLAR
# =========================

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    try:

        save_user(message.from_user)

        bot.send_message(
            message.chat.id,
            "ℹ️ Iltimos, menyudagi tugmalardan foydalaning.",
            reply_markup=main_menu()
        )

    except Exception as e:

        print("MESSAGE ERROR:", e)


# =========================
# ISHGA TUSHIRISH
# =========================

if name == "main":

    print("🗄️ Database ishga tushmoqda...")

    init_database()

    print("🤖 Bot ishga tushdi!")
    print("✅ Foydalanuvchilarni kutmoqda...")

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
