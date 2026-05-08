import os
import threading
import time
import asyncio
from flask import Flask
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return "Zouhair Bot is Alive!"

def run_bot_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            loop.run_until_complete(
                bot.send_message(chat_id=CHAT_ID, text="🚀 البوت خدام يا زهير! تم التشغيل بنجاح")
            )
            print("Message sent successfully")
        except Exception as e:
            print(f"Error sending message: {e}")
        time.sleep(300)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
