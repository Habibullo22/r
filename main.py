import telebot
from telebot import types

from config import BOT_TOKEN
from database import init_database, save_user


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
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    try:
        # Foydalanuvchini bazaga saqlash
        save_user(message.from_user)

        bot.send_message(
            message.chat.id,
            "👋 Assalomu alaykum!\n\n"
            "🔎 <b>Telegram Search Bot</b>ga xush kelibsiz!\n\n"
            "Bu yerda tarif sotib olib, mavjud Telegram ma’lumotlari "
            "doirasida qidiruv xizmatlaridan foydalanishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

    except Exception as e:
        print("START ERROR:", e)

        bot.send_message(
            message.chat.id,
            "❌ Xatolik yuz berdi. Keyinroq qayta urinib ko‘ring."
        )


# =========================
# BUTTONLAR
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    if call.data == "search_user":

        bot.answer_callback_query(call.id)

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

    elif call.data == "groups":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "👥 <b>Guruhlar</b>\n\n"
            "Bu bo‘lim keyingi bosqichda real qidiruv tizimiga ulanadi.",
            parse_mode="HTML"
        )

    elif call.data == "channels":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "📢 <b>Kanallar</b>\n\n"
            "Bu bo‘lim keyingi bosqichda real qidiruv tizimiga ulanadi.",
            parse_mode="HTML"
        )

    elif call.data == "messages":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "💬 <b>Qayerda yozgan</b>\n\n"
            "Bu bo‘lim keyingi bosqichda real qidiruv tizimiga ulanadi.",
            parse_mode="HTML"
        )

    elif call.data == "reactions":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "❤️ <b>Reaksiyalar</b>\n\n"
            "Bu bo‘lim keyingi bosqichda real qidiruv tizimiga ulanadi.",
            parse_mode="HTML"
        )

    elif call.data == "full_info":

        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "📊 <b>To‘liq ma’lumot</b>\n\n"
            "Bu bo‘lim barcha mavjud qidiruv natijalarini bir joyda ko‘rsatadi.",
            parse_mode="HTML"
        )

    elif call.data == "tariffs":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "💳 <b>Tariflar</b>\n\n"
            "Tariflar tizimi keyingi bosqichda qo‘shiladi.",
            parse_mode="HTML"
        )

# =========================
# XATOLIKLARNI KO‘RISH
# =========================

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    save_user(message.from_user)

    bot.send_message(
        message.chat.id,
        "ℹ️ Iltimos, menyudagi tugmalardan foydalaning.",
        reply_markup=main_menu()
    )


# =========================
# ISHGA TUSHIRISH
# =========================

if name == "main":

    print("🗄️ Database ishga tushmoqda...")
    init_database()

    print("🤖 Bot ishga tushdi...")
    print("✅ /start kutilyapti...")

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
