import telebot
from config import BOT_TOKEN

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida ko‘rsatilmagan!")

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "🔎 Telegram Search Bot'ga xush kelibsiz!"
    )


print("🤖 Bot ishga tushdi...")
bot.infinity_polling()
