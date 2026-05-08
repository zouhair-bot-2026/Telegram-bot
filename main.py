import os
import time
import asyncio
# import yfinance as yf
# import pandas as pd
# import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, time as dt_time
# import pytz
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
# TUNISIA_TZ = pytz.timezone('Africa/Tunis')

PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "EURCHF": "EURCHF=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "EURGBP": "EURGBP=X",
    "USDCHF": "USDCHF=X",
    "EURJPY": "EURJPY=X"
}

# Flask باش Render ما يقتلش البوت
app = Flask('')

@app.route('/')
def home():
    return "بوت الفوركس شغال ✅"

def run_flask():
    port = int(os.environ.get('PORT', 8080))  # ← هذا السطر تبدل
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_sma(data, window):
    return data.rolling(window=window).mean()

def calculate_ema(data, window):
    return data.ewm(span=window, adjust=False).mean()

def get_trend(df):
    if len(df) < 50:
        return "غير محدد"
    sma20 = df['SMA20'].iloc[-1]
    sma50 = df['SMA50'].iloc[-1]
    close = df['Close'].iloc[-1]
    
    if close > sma20 > sma50:
        return "صاعد 📈"
    elif close < sma20 < sma50:
        return "هابط 📉"
    else:
        return "عرضي ↔️"

def analyze_pair(pair):
    try:
        symbol = PAIRS
        df = yf.download(symbol, period="5d", interval="1h", progress=False, threads=False)
        time.sleep(1)

        if df.empty or len(df) < 50:
            return None

        df['RSI'] = calculate_rsi(df['Close'])
        df['SMA20'] = calculate_sma(df['Close'], 20)
        df['SMA50'] = calculate_sma(df['Close'], 50)
        df['EMA9'] = calculate_ema(df['Close'], 9)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        signal = None
        reason = ""
        confidence = ""

        # شروط الشراء القوية
        if (last['RSI'] < 30 and
            last['Close'] > last['SMA20'] and
            prev['Close'] <= prev['SMA20'] and
            last['Close'] > last['EMA9']):
            signal = "شراء قوي 🟢🟢"
            reason = "RSI تشبع بيعي + اختراق SMA20 + فوق EMA9"
            confidence = "85%"

        # شروط الشراء العادية
        elif (last['RSI'] < 35 and
              last['Close'] > last['SMA20'] and
              prev['Close'] <= prev['SMA20']):
            signal = "شراء 🟢"
            reason = "RSI قريب تشبع + اختراق SMA20"
            confidence = "70%"

        # شروط البيع القوية
        elif (last['RSI'] > 70 and
              last['Close'] < last['SMA20'] and
              prev['Close'] >= prev['SMA20'] and
              last['Close'] < last['EMA9']):
            signal = "بيع قوي 🔴🔴"
            reason = "RSI تشبع شرائي + كسر SMA20 + تحت EMA9"
            confidence = "85%"

        # شروط البيع العادية
        elif (last['RSI'] > 65 and
              last['Close'] < last['SMA20'] and
              prev['Close'] >= prev['SMA20']):
            signal = "بيع 🔴"
            reason = "RSI قريب تشبع + كسر SMA20"
            confidence = "70%"

        if signal:
            trend = get_trend(df)
            now_tunis = datetime.now(TUNISIA_TZ).strftime("%H:%M")
            msg = f"🚨 إشارة {signal}\n\n"
            msg += f"الزوج: {pair}\n"
            msg += f"السعر: {last['Close']:.5f}\n"
            msg += f"RSI: {last['RSI']:.1f}\n"
            msg += f"SMA20: {last['SMA20']:.5f}\n"
            msg += f"الاتجاه: {trend}\n"
            msg += f"السبب: {reason}\n"
            msg += f"الثقة: {confidence}\n"
            msg += f"الوقت: {now_tunis} 🇹🇳"
            return msg
        return None

    except Exception as e:
        print(f"Error analyzing {pair}: {e}")
        return None

async def send_signals(context: ContextTypes.DEFAULT_TYPE):
    print(f"Checking signals... {datetime.now(TUNISIA_TZ)}")
    signals_found = 0
    for pair in PAIRS.keys():
        try:
            msg = analyze_pair(pair)
            if msg:
                await context.bot.send_message(chat_id=CHAT_ID, text=msg)
                signals_found += 1
                await asyncio.sleep(5)
        except Exception as e:
            print(f"Error sending {pair}: {e}")
    
    if signals_found == 0:
        print("No signals this hour")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 فحص لحظي لـ3 أزواج... استنى 15 ثانية ⏳")
    test_pairs = ["EURUSD", "EURCHF", "AUDUSD"]
    results = []
    
    for pair in test_pairs:
        try:
            result = analyze_pair(pair)
            if result:
                results.append(result)
            else:
                symbol = PAIRS
                df = yf.download(symbol, period="2d", interval="1h", progress=False, threads=False)
                time.sleep(1)
                if not df.empty and len(df) > 14:
                    df['RSI'] = calculate_rsi(df['Close'])
                    rsi = df['RSI'].iloc[-1]
                    close = df['Close'].iloc[-1]
                    results.append(f"⚪ {pair}\nالسعر: {close:.5f}\nRSI: {rsi:.1f} - لا توجد إشارة حاليا")
                else:
                    results.append(f"❌ {pair}: مافماش داتا كافية")
        except Exception as e:
            results.append(f"❌ {pair}: Error {str(e)[:30]}")
        await asyncio.sleep(5)

    final_msg = "📊 نتيجة الفحص الفوري:\n\n" + "\n\n".join(results)
    await update.message.reply_text(final_msg)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = "🤖 بوت الفوركس شغال 24/7 ✅\n\n"
    welcome_msg += "📈 الأزواج: 10\n"
    welcome_msg += "⏰ الإشارات: كل ساعة\n"
    welcome_msg += "📊 الملخص اليومي: 22:00 🇹🇳\n\n"
    welcome_msg += "الأوامر:\n"
    welcome_msg += "/test - فحص فوري\n"
    welcome_msg += "/start - هذه الرسالة"
    await update.message.reply_text(welcome_msg)

async def daily_summary(context: ContextTypes.DEFAULT_TYPE):
    now_tunis = datetime.now(TUNISIA_TZ).strftime("%Y-%m-%d")
    summary = f"📊 ملخص يومي {now_tunis} 🇹🇳\n\n"
    summary += "✅ البوت شغال طبيعي\n"
    summary += "📈 يراقب 10 أزواج\n"
    summary += "⏰ فحص كل ساعة\n\n"
    summary += "غدوة يوم جديد و فرص جديدة 💪"
    await context.bot.send_message(chat_id=CHAT_ID, text=summary)

async def run_bot():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("test", test_command))

    job_queue = application.job_queue
    job_queue.run_repeating(send_signals, interval=3600, first=10)
    job_queue.run_daily(daily_summary, time=dt_time(hour=22, minute=0, tzinfo=TUNISIA_TZ))

    print("Bot started successfully...")
    await application.run_polling()

if __name__ == '__main__':
    # ---- Dummy web server for Render ----
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Bot is running')
    
    def run_server():
        server = HTTPServer(('0.0.0.0', 10000), Handler)
        server.serve_forever()
    
    threading.Thread(target=run_server, daemon=True).start()
    # ---- End dummy server ----
    
    asyncio.run(run_bot())
