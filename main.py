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
    print(">> نحاول نبعث للـ Telegram...")
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("خطأ: TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID فارغ في Environment Variables")
            return
            
        now = datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': f'تم الارسال: {now}'}
        r = requests.post(url, data=data, timeout=10)
        
        print(f'تم الارسال: {now} | Status Code: {r.status_code}')
        print(f'Response من Telegram: {r.text}')
        
    except Exception as e:
        print(f'خطأ في الارسال: {e}')

def run_schedule():
    schedule.every(1).minutes.do(send_telegram_message)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def home():
    return 'Bot is running'

# هذا يخلي الكود يخدم مع Render
thread_started = False
@app.before_request
def start_thread():
    global thread_started
    if not thread_started:
        print(">> باش نشغل الـ Thread متاع الارسال")
        Thread(target=run_schedule, daemon=True).start()
        send_telegram_message() # اول رسالة فورية
        thread_started = True

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
