import os
import time
import requests
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") 
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# الأزواج الجديدة - 10 أزواج
PAIRS = {
    "EUR/USD": "EURUSD=X",
    "EUR/CHF": "EURCHF=X", 
    "AUD/USD": "AUDUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "EUR/JPY": "EURJPY=X",
    "CAD/JPY": "CADJPY=X",
    "AUD/CAD": "AUDCAD=X",
    "EUR/AUD": "EURAUD=X",
    "AUD/JPY": "AUDJPY=X"  # بدلنا TND/USD
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def check_signals():
    for name, ticker in PAIRS.items():
        try:
            df = yf.download(ticker, period="5d", interval="1h", progress=False)
            if df.empty or len(df) < 50:
                continue
                
            df["RSI"] = ta.rsi(df["Close"], length=14)
            macd = ta.macd(df["Close"])
            df["MACD"] = macd["MACD_12_26_9"]
            df["MACD_S"] = macd["MACDs_12_26_9"]
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            rsi = last["RSI"]
            macd_cross_up = prev["MACD"] < prev["MACD_S"] and last["MACD"] > last["MACD_S"]
            macd_cross_down = prev["MACD"] > prev["MACD_S"] and last["MACD"] < last["MACD_S"]
            green_candle = last["Close"] > last["Open"]
            red_candle = last["Close"] < last["Open"]
            
            signal = None
            if rsi < 35 and macd_cross_up and green_candle:
                signal = "CALL 🟢"
            elif rsi > 65 and macd_cross_down and red_candle:
                signal = "PUT 🔴"
            
            if signal:
                msg = f"""
🚨 *فرصة يا زهير*
الزوج: *{name}*
الإشارة: *{signal}*
RSI: `{rsi:.1f}`
MACD: تقاطع
السعر: `{last['Close']:.5f}`
الفريم: 1H
المدة المقترحة: 1-3 ساعات
"""
                send_telegram(msg)
                time.sleep(1)
                
        except Exception as e:
            print(f"Error {name}: {e}")

def run_bot():
    send_telegram("🚀 بوت الإشارات خدام يا زهير! نعس على 10 أزواج كل ساعة.")
    while True:
        check_signals()
        time.sleep(3600)  # كل ساعة

@app.route('/')
def home():
    return "Zouhair Signals Bot is Alive!"

if __name__ == "__main__":
    Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=PORT)
