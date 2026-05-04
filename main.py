import telebot
import yfinance as yf
import pandas as pd
import time
from threading import Thread

TOKEN = "8235557002:AAEI3vbN3UrJ2CrFjGU2R37ErcXEUpQmIBc"
bot = telebot.TeleBot(TOKEN)
CHAT_ID = None

# الازواج مع الرموز الصحيحة متاع yfinance
PAIRS = {
    "EUR/USD OTC": "EURUSD=X",
    "USD/JPY OTC": "JPY=X", 
    "AUD/USD OTC": "AUDUSD=X",
    "EUR/AUD OTC": "EURAUD=X",
    "EUR/JPY OTC": "EURJPY=X", 
    "EUR/CHF OTC": "EURCHF=X",
    "GOLD OTC": "GC=F",
    "SILVER OTC": "SI=F",
    "CAD/JPY OTC": "CADJPY=X"
}

def analyze_pair(name, symbol):
    try:
        data = yf.download(symbol, period="30d", interval="4h")
        if data.empty:
            return None
            
        # RSI 14
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        last_rsi = rsi.iloc[-1]
        
        # MACD 12-26-9
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        last_macd = macd.iloc[-1]
        last_signal = signal.iloc[-1]
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]
        
        # شرط الشراء: RSI <= 30 + تقاطع MACD لفوق
        if last_rsi <= 30 and prev_macd < prev_signal and last_macd > last_signal:
            return f"🟢 شراء {name}\nRSI: {last_rsi:.2f} تشبع بيعي\nMACD: تقاطع ايجابي\nفريم: 4H"
        
        # شرط البيع: RSI >= 70 + تقاطع MACD لتحت  
        elif last_rsi >= 70 and prev_macd > prev_signal and last_macd < last_signal:
            return f"🔴 بيع {name}\nRSI: {last_rsi:.2f} تشبع شرائي\nMACD: تقاطع سلبي\nفريم: 4H"
            
    except Exception as e:
        print(f"Error {name}: {e}")
    return None

def check_all_signals():
    global CHAT_ID
    while True:
        if CHAT_ID:
            signals = []
            for name, symbol in PAIRS.items():
                result = analyze_pair(name, symbol)
                if result:
                    signals.append(result)
                time.sleep(2)
            
            if signals:
                msg = "🔥 اشارات جديدة 🔥\n\n" + "\n\n".join(signals)
                bot.send_message(CHAT_ID, msg)
        
        time.sleep(14400)  # كل 4 ساعات

@bot.message_handler(commands=['start'])
def start(message):
    global CHAT_ID
    CHAT_ID = message.chat.id
    bot.reply_to(message, "تم تشغيل بوت التحليل ✅\nنراقب 9 ازواج فريم 4H\nRSI 14 + MACD 12-26-9\nباش نبعثلك كي نلقى فرصة")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.reply_to(message, "جاري الفحص توا...")
    signals = []
    for name, symbol in PAIRS.items():
        result = analyze_pair(name, symbol)
        if result:
            signals.append(result)
        time.sleep(1)
    
    if signals:
        msg = "🔥 اشارات حالية 🔥\n\n" + "\n\n".join(signals)
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, "لا توجد اشارات حاليا على فريم 4H")

Thread(target=check_all_signals).start()
bot.infinity_polling()
