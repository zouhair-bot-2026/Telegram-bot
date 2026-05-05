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
            data = yf.download(tickers=pair, period='30d', interval='4h', progress=False)
            if len(data) < 200: continue # لازم داتا كافية للـ EMA200
            
            data = calculate_indicators(data)
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            name = pair.replace('USDJPY=X', 'USD/JPY').replace('EURUSD=X', 'EUR/USD').replace('USDCAD=X', 'USD/CAD').replace('EURAUD=X', 'EUR/AUD').replace('EURJPY=X', 'EUR/JPY').replace('XAUUSD=X', 'GOLD')
            
            signal = None
            
            # شرط الشراء: RSI < 30 + تقاطع MACD لفوق + السعر فوق EMA200
            buy_condition = (last['RSI'] < 30 and 
                             prev['MACD'] < prev['Signal'] and 
                             last['MACD'] > last['Signal'] and 
                             last['Close'] > last['EMA200'])
            
            # شرط البيع: RSI > 70 + تقاطع MACD لتحت + السعر تحت EMA200  
            sell_condition = (last['RSI'] > 70 and 
                              prev['MACD'] > prev['Signal'] and 
                              last['MACD'] < last['Signal'] and 
                              last['Close'] < last['EMA200'])
            
            if buy_condition:
                signal = f"✅ شراء قوي {name}\nالسعر: {last['Close']:.5f}\nRSI: {last['RSI']:.2f} | MACD تقاطع صعودي\nفلتر: فوق EMA200"
            elif sell_condition:
                signal = f"❌ بيع قوي {name}\nالسعر: {last['Close']:.5f}\nRSI: {last['RSI']:.2f} | MACD تقاطع هبوطي\nفلتر: تحت EMA200"
            
            if signal:
                bot.send_message(CHAT_ID, f"🚨 إشارة 4H مفلترة\n{signal}")
                
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
