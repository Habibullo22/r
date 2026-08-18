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


# ==================================================
# TEKSHIRUV
# ==================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID topilmadi!")


# ==================================================
# BOT
# ==================================================

bot = telebot.TeleBot(BOT_TOKEN)


# ==================================================
# TELEGRAM ACCOUNT CLIENT
# ==================================================

telegram_client = create_client()


# ==================================================
# CHEK KUTILAYOTGAN FOYDALANUVCHILAR
# ==================================================

waiting_receipt = {}


# ==================================================
# ASOSIY MENYU
# ==================================================

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


# ==================================================
# TARIFLAR
# ==================================================

def tariffs_menu():

    markup = types.InlineKeyboardMarkup(row_width=1)

    tariffs = get_tariffs()

    for tariff in tariffs:

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

    markup.add(
        types.InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="back_main"
        )
    )

    return markup


# ==================================================
# START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    try:

        save_user(message.from_user)

        bot.send_message(
            message.chat.id,

            "👋 <b>Assalomu alaykum!</b>\n\n"
            "🔎 <b>Telegram Search Bot</b>ga xush kelibsiz!\n\n"
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


# ==================================================
# ODDIY CALLBACKLAR
#
# MUHIM:
# approve_ va reject_ BU HANDLERGA KIRMAYDI
# ==================================================

@bot.callback_query_handler(
    func=lambda call:
        not call.data.startswith("approve_")
        and not call.data.startswith("reject_")
)
def callbacks(call):

    user_id = call.from_user.id

    try:

        # ==================================================
        # TARIFLAR
        # ==================================================

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

            return

        # ==================================================
        # TARIF TANLASH
        # ==================================================

        if call.data.startswith("tariff_"):

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

            tariff_id = tariff[0]
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
                f"⏳ Muddati: <b>{days} kun</b>\n\n"
                "Sotib olish uchun tugmani bosing."
            ).replace(",", " ")

            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=markup
            )

            return

        # ==================================================
        # SOTIB OLISH
        # ==================================================

        if call.data.startswith("buy_"):

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

        # ==================================================
        # CHEK YUBORISH
        # ==================================================

        if call.data.startswith("receipt_"):

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

            return

        # ==================================================
        # QIDIRUV
        # ==================================================

        if call.data == "search_user":

            bot.answer_callback_query(call.id)

            if not has_active_tariff(user_id):

                bot.send_message(
                    call.message.chat.id,

                    "🔒 <b>Qidiruv yopiq.</b>\n\n"
                    "Qidiruvdan foydalanish uchun "
                    "avval tarif sotib oling.",

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

            return

        # ==================================================
        # GURUHLAR
        # ==================================================

        if call.data == "groups":

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

                "👥 <b>Guruhlar</b>\n\n"
                "Qidiruv moduli ulanmoqda.",

                parse_mode="HTML"
            )

            return

        # ==================================================
        # KANALLAR
        # ==================================================

        if call.data == "channels":

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

                "📢 <b>Kanallar</b>\n\n"
                "Qidiruv moduli ulanmoqda.",

                parse_mode="HTML"
            )

            return

        # ==================================================
        # XABARLAR
        # ==================================================

        if call.data == "messages":

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

                "💬 <b>Qayerda yozgan</b>\n\n"
                "Qidiruv moduli ulanmoqda.",

                parse_mode="HTML"
            )

            return

        # ==================================================
        # REAKSIYALAR
        # ==================================================

        if call.data == "reactions":

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

                "❤️ <b>Reaksiyalar</b>\n\n"
                "Mavjud Telegram ma’lumotlari "
                "doirasida tekshiriladi.",

                parse_mode="HTML"
            )

            return

        # ==================================================
        # TO‘LIQ MA'LUMOT
        # ==================================================

        if call.data == "full_info":

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

                "📊 <b>To‘liq ma’lumot</b>\n\n"
                "Qidiruv natijalari shu bo‘limda "
                "birlashtiriladi.",

                parse_mode="HTML"
            )

            return

        # ==================================================
        # ORQAGA
        # ==================================================

        if call.data == "back_main":

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
                "🏠 <b>Asosiy menyu</b>\n\n"
                "Kerakli bo‘limni tanlang:",

                call.message.chat.id,
                call.message.message_id,

                parse_mode="HTML",
                reply_markup=main_menu()
            )

            return

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


# ==================================================
# CHEK QABUL QILISH
# ==================================================

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

        waiting_receipt.pop(user_id, None)

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
        username_text = f"@{username}"
    else:
        username_text = "Username yo‘q"

    try:
        tariff_name = purchase[7]
        price = purchase[8]
    except Exception:
        tariff_name = "Noma’lum"
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
        "✅ Chekingiz adminga yuborildi.\n\n"
        "⏳ Tasdiqlanishini kuting."
    )

    waiting_receipt.pop(user_id, None)


# ==================================================
# ADMIN TASDIQLASH / RAD ETISH
#
# BU HANDLER UMUMIY CALLBACKDAN OLDIN
# RO‘YXATDAN O‘TKAZILADI
# ==================================================

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

        # ==================================================
        # TASDIQLASH
        # ==================================================

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
                days = purchase[9]
            except Exception:
                tariff_name = "Tarif"
                days = 0

            bot.send_message(
                user_id,

                "🎉 <b>To‘lov tasdiqlandi!</b>\n\n"
                f"📦 Tarif: <b>{tariff_name}</b>\n"
                f"⏳ Muddat: <b>{days} kun</b>\n\n"
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

            print(
                f"PAYMENT APPROVED: {purchase_id}"
            )

            return

        # ==================================================
        # RAD ETISH
        # ==================================================

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


# ==================================================
# BOSHQA XABARLAR
# ==================================================

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    try:

        save_user(
            message.from_user
        )

        bot.send_message(
            message.chat.id,
            "ℹ️ Menyudagi tugmalardan foydalaning.",
            reply_markup=main_menu()
        )

    except Exception as e:

        print(
            "MESSAGE ERROR:",
            repr(e)
        )


# ==================================================
# ISHGA TUSHIRISH
# ==================================================

if __name__ == "__main__":

    print("================================")
    print("🗄️ DATABASE ISHGA TUSHMOQDA")
    print("================================")

    init_database()

    print("================================")
    print("🤖 TELEGRAM SEARCH BOT")
    print("================================")
    print("✅ BOT ISHGA TUSHDI")
    print("================================")

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
