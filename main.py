import requests
import schedule
import time
import os
import threading
from flask import Flask
from datetime import datetime

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram_message():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"✅ البوت خدام تمام\nالتوقيت: {now}\nمن Render Python 3.14"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
        print("تم الارسال:", now)
    except Exception as e:
        print("فشل الارسال:", e)

def run_schedule():
    schedule.every(1).hours.do(send_telegram_message)
    send_telegram_message()  # يبعث أول رسالة كي يخدم
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.route('/')
def home():
    return "Bot is alive!"

if __name__ == "__main__":
    threading.Thread(target=run_schedule, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
