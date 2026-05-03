import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get('BOT_TOKEN')
app = Flask(__name__)

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('البوت متاع Zouhair يخدم 🔥')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# Flask route عشان Render
@app.route('/')
def home():
    return 'Bot is running!'

def main():
    # Create Application
        # Create Application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
