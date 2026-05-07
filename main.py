from flask import Flask
from threading import Thread
import os
import telebot
import yfinance as yf
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import time
import sys

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = os.environ.get('TOKEN')
CHAT_ID = '8513844345' 
bot = telebot.TeleBot(TOKEN)

# 1. الأزواج الـ10 الجداد متاعك
PAIRS = [
    'EURUSD=X', 'EURCHF=X', 'AUDUSD=X', 'USDJPY=X', 'USDCHF=X', 
    'EURJPY=X', 'CADJPY=X', 'AUDCAD=X', 'EURAUD=X', 'XAUUSD=X'
]

def check_signals():
    print("Starting 1H scan...") 
    for pair in PAIRS:
        try:
            # نظفو الاسم للعرض
            name = pair.replace('=X', '').replace('USD', 'USD/').replace('XAU', 'GOLD ')
            print(f"Checking {name} 1H...") 
            
            # 2. بدلنا الفريم لـ 1H و نقصنا المدة لـ 20 يوم تكفي
            data = yf.download(tickers=pair, period="20d", interval="1h", progress=False)
            if data.empty or len(data) < 50: # 50 شمعة تكفي للـ RSI و MACD
                print(f"Not enough data for {name}")
                continue

            # 3. نحينا EMA200 خلاص. خلينا RSI + MACD فقط
            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            data["RSI"] = 100 - (100 / (1 + rs))
            exp1 = data["Close"].ewm(span=12, adjust=False).mean()
            exp2 = data["Close"].ewm(span=26, adjust=False).mean()
            data["MACD"] = exp1 - exp2
            data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            price = round(last["Close"], 5)
            
            # ATR للستوب و الهدف
            data['H-L'] = data['High'] - data['Low']
            data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
            data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
            data['TR'] = data[['H-L','H-PC','L-PC']].max(axis=1)
            atr = data['TR'].rolling(14).mean().iloc[-1]
            sl_distance = round(atr * 1.5, 5)

            # 4. شروط الشراء الجديدة: RSI + MACD فقط بلا EMA200
            buy_condition = (
                last["RSI"] > 50 and 
                prev["MACD"] < prev["Signal"] and 
                last["MACD"] > last["Signal"]
            )
            
            # شروط البيع الجديدة: RSI + MACD فقط بلا EMA200
            sell_condition = (
                last["RSI"] < 50 and 
                prev["MACD"] > prev["Signal"] and 
                last["MACD"] < last["Signal"]
            )

            if buy_condition:
                sl = round(price - sl_distance, 5)
                tp = round(price + sl_distance * 2, 5)
                # 5. زدنا المدة 20 دقيقة في الرسالة
                msg = f"🟢 شراء {name}\n⏰ المدة: 20 دقيقة\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)
                print(f"SIGNAL SENT: BUY {name}")
                
            elif sell_condition:
                sl = round(price + sl_distance, 5)
                tp = round(price - sl_distance * 2, 5)
                # 5. زدنا المدة 20 دقيقة في الرسالة
                msg = f"🔴 بيع {name}\n⏰ المدة: 20 دقيقة\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)
                print(f"SIGNAL SENT: SELL {name}")

        except Exception as e:
            print(f"Error with {pair}: {e}")
            
    print("Scan finished. Waiting for next 1H candle.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"بوت إشارات 1H V3 خدام 🔥\nالفلاتر: RSI + MACD\nالمدة: 20 دقيقة\nنراقب في: 10 أزواج منهم الذهب")

# نظفتلك الكود من التكرار اللي كان فيه
tunis_tz = pytz.timezone('Africa/Tunis')
scheduler = BackgroundScheduler(timezone=tunis_tz)

# 6. بدلنا التوقيت: كل ساعة يخدم بعد تسكيرة الشمعة بدقيقة
scheduler.add_job(check_signals, 'cron', minute=1) 
scheduler.start()

bot.remove_webhook()
time.sleep(1)
print("Bot V3 is running and scheduler started...")
sys.stdout.flush()
keep_alive()
bot.infinity_polling(skip_pending=True)
