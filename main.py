import requests
import os
import schedule
import time
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz

app = Flask(__name__)

def send_telegram_message():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    tunis_tz = pytz.timezone('Africa/Tunis')
    now = datetime.now(tunis_tz).strftime("%Y-%m-%d %H:%M:%S")
    message = f"تم الارسال: {now}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, json=payload)
        print(message)  # باش يطلع في الـ Logs
    except Exception as e:
        print(f"خطأ في الارسال: {e}")

def run_schedule():
    # ابعث رسالة فورية أول ما يخدم
    send_telegram_message()
    # بعدها ابعث كل دقيقة
    schedule.every(1).minutes.do(send_telegram_message)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def home():
    return "Telegram Bot is Running"

if __name__ == "__main__":
    # شغل الـ schedule في thread منفصل
    Thread(target=run_schedule).start()
    # شغل Flask باش Render ما يقتلش البوت
    app.run(host='0.0.0.0', port=10000)
