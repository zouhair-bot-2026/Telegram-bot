import os
from threading import Thread
from flask import Flask

app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))).start()

# الكود متاعك القديم يبدا من هنا لتحت 👇
# ما تمس منو شي
import telebot
import yfinance as yf
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = os.environ.get('TOKEN')
CHAT_ID = '8513844345' 

bot = telebot.TeleBot(TOKEN)

PAIRS = ['EURUSD=X', 'USDJPY=X', 'USDCAD=X', 'EURAUD=X', 'EURJPY=X', 'XAUUSD=X']

def calculate_indicators(data):
    # RSI
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    # EMA200 فلتر الترند
    data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()
    return data

def check_signals():
    for pair in PAIRS:
        try:
            data = yf.download(tickers=pair, period="60d", interval="4h", progress=False)
            if data.empty or len(data) < 210:
                continue

            # نحسبو المؤشرات
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
            
            # نحسبو ATR للستوب و الهدف
            data['H-L'] = data['High'] - data['Low']
            data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
            data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
            data['TR'] = data[['H-L','H-PC','L-PC']].max(axis=1)
            atr = data['TR'].rolling(14).mean().iloc[-1]
            sl_distance = round(atr * 1.5, 5)  # ستوب = 1.5 × ATR
            tp_distance = round(sl_distance * 2, 5)  # هدف = ضعف الستوب

            name = pair.replace('=X', '').replace('USD', 'USD/')

            # شروط الشراء: فوق EMA200 + RSI>50 + تقاطع MACD لفوق
            buy_condition = (last["Close"] > last["EMA200"] and 
                             last["RSI"] > 50 and 
                             prev["MACD"] < prev["Signal"] and 
                             last["MACD"] > last["Signal"])
            
            # شروط البيع: تحت EMA200 + RSI<50 + تقاطع MACD لتحت
            sell_condition = (last["Close"] < last["EMA200"] and 
                              last["RSI"] < 50 and 
                              prev["MACD"] > prev["Signal"] and 
                              last["MACD"] < last["Signal"])

            if buy_condition:
                sl = round(price - sl_distance, 5)
                tp = round(price + tp_distance, 5)
                msg = f"🟢 شراء {name}\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)
                
            elif sell_condition:
                sl = round(price + sl_distance, 5)
                tp = round(price - tp_distance, 5)
                msg = f"🔴 بيع {name}\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)

        except Exception as e:
            print(f"Error with {pair}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(check_signals, 'interval', hours=4)
scheduler.start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"بوت إشارات 4H V2 خدام 🔥\nالفلاتر: RSI + MACD + EMA200\nنراقب في: EUR/USD, USD/JPY, USD/CAD, EUR/AUD, EUR/JPY, GOLD")

print("Bot V2 is running...")
bot.infinity_polling()
