import os
from threading import Thread
from flask import Flask
import telebot
import yfinance as yf
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))).start()

TOKEN = os.environ.get('TOKEN')
CHAT_ID = '8513844345'
bot = telebot.TeleBot(TOKEN)

PAIRS = ['EURUSD=X', 'USDJPY=X', 'USDCAD=X', 'EURAUD=X', 'EURJPY=X', 'XAUUSD=X']

def check_signals():
    print("Starting 4H scan...") # هذا بش يطلع في Logs
    for pair in PAIRS:
        try:
            name = pair.replace('=X', '').replace('USD', 'USD/')
            print(f"Checking {name} 4H...") # هذا بش يطلع في Logs
            
            data = yf.download(tickers=pair, period="60d", interval="4h", progress=False)
            if data.empty or len(data) < 210: 
                print(f"Not enough data for {name}")
                continue

            # المؤشرات
            data["EMA200"] = data["Close"].ewm(span=200).mean()
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
            
            # شروط الشراء
            buy_condition = (last["Close"] > last["EMA200"] and last["RSI"] > 50 and 
                           prev["MACD"] < prev["Signal"] and last["MACD"] > last["Signal"])
            # شروط البيع  
            sell_condition = (last["Close"] < last["EMA200"] and last["RSI"] < 50 and 
                            prev["MACD"] > prev["Signal"] and last["MACD"] < last["Signal"])

            if buy_condition:
                sl = round(price - sl_distance, 5)
                tp = round(price + sl_distance * 2, 5)
                msg = f"🟢 شراء {name}\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)
                print(f"SIGNAL SENT: BUY {name}")
            elif sell_condition:
                sl = round(price + sl_distance, 5)
                tp = round(price - sl_distance * 2, 5)
                msg = f"🔴 بيع {name}\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)
                print(f"SIGNAL SENT: SELL {name}")

        except Exception as e:
            print(f"Error with {pair}: {e}")
    
    print("Scan finished. Waiting for next 4H candle.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"بوت إشارات 4H V2 خدام 🔥\nالفلاتر: RSI + MACD + EMA200\nنراقب في: EUR/USD, USD/JPY, USD/CAD, EUR/AUD, EUR/JPY, GOLD")

# نشغلو الـ Scheduler بالتوقيت الصحيح متاع الشموع
tunis_tz = pytz.timezone('Africa/Tunis')
scheduler = BackgroundScheduler(timezone=tunis_tz)
# 1,5,9,13,17,21 بتوقيت تونس = بعد تسكيرة شمعة 4H بدقيقة
scheduler.add_job(check_signals, 'cron', hour='1,5,9,13,17,21', minute=1)
scheduler.start()

print("Bot V2 is running and scheduler started...")
bot.infinity_polling()
