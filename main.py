import os
import requests
import schedule
import time
from datetime import datetime
from threading import Thread
from flask import Flask
import pytz

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TZ = pytz.timezone('Africa/Tunis')

def send_telegram_message():
    try:
        now = datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': f'تم الارسال: {now}'}
        requests.post(url, data=data, timeout=10)
        print(f'تم الارسال: {now}')
    except Exception as e:
        print(f'خطأ: {e}')

def run_schedule():
    schedule.every(1).minutes.do(send_telegram_message)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def home():
    return 'Bot is running'

# هذا يشتغل مع gunicorn
thread_started = False
@app.before_request
def start_thread():
    global thread_started
    if not thread_started:
        Thread(target=run_schedule, daemon=True).start()
        send_telegram_message() # اول رسالة
        thread_started = True

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
