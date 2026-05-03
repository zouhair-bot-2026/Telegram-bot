import os
from telegram.ext import Application, CommandHandler

TOKEN = os.environ.get('BOT_TOKEN')

async def start(update, context):
    await update.message.reply_text('البوت متاع Zouhair يخدم 🔥')

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

PORT = int(os.environ.get('PORT', 10000))
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=f"https://zouhair-telegram-bot.onrender.com/{TOKEN}"
)
