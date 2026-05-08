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
from datetime import datetime

app = Flask('')

@app.route('/')
def home():
    return "Bot V3 is alive!"

def keep_alive():
    def run_flask():
        app.run(host='0.0.0.0', port=10000)
    t = Thread(target=run_flask)
    t.start()

TOKEN = os.environ.get('TOKEN')
CHAT_ID = '8513844345'
bot = telebot.TeleBot(TOKEN)

# 1. الأزواج الـ10
PAIRS = [
    'EURUSD=X', 'EURCHF=X', 'AUDUSD=X', 'USDJPY=X', 'USDCHF=X',
    'EURJPY=X', 'CADJPY=X', 'AUDCAD=X', 'EURAUD=X', 'XAUUSD=X'
]

def check_signals():
    print("🔍 Starting 1H scan...")
    signals_sent = 0
    
    for pair in PAIRS:
        try:
            name = pair.replace('=X', '').replace('XAUUSD', 'GOLD')
            print(f"Checking {name} 1H...")
            
            data = yf.download(tickers=pair, period="20d", interval="1h", progress=False, threads=False)
            
            if data.empty or len(data) < 50:
                print(f"❌ Not enough data for {name}")
                time.sleep(3)  # مهم حتى كان فشل
                continue

            # RSI
            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            data["RSI"] = 100 - (100 / (1 + rs))
            
            # MACD
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
            
            # شروط الشراء: RSI + MACD فقط
            buy_condition = (
                last["RSI"] > 50 and 
                prev["MACD"] < prev["Signal"] and 
                last["MACD"] > last["Signal"]
            )
            
            # شروط البيع: RSI + MACD فقط
            sell_condition = (
                last["RSI"] < 50 and 
                prev["MACD"] > prev["Signal"] and 
                last["MACD"] < last["Signal"]
            )
            
            if buy_condition:
                sl = round(price - sl_distance, 5)
                tp = round(price + sl_distance * 2, 5)
                msg = f"🟢 شراء {name}\n⏰ المدة: 20 دقيقة\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)
                print(f"✅ SIGNAL SENT: BUY {name}")
                signals_sent += 1
                
            elif sell_condition:
                sl = round(price + sl_distance, 5)
                tp = round(price - sl_distance * 2, 5)
                msg = f"🔴 بيع {name}\n⏰ المدة: 20 دقيقة\nالسعر: {price}\nSL: {sl}\nTP: {tp}\nRR: 1:2"
                bot.send_message(CHAT_ID, msg)
                print(f"✅ SIGNAL SENT: SELL {name}")
                signals_sent += 1
            else:
                print(f"✅ {name} - لا توجد إشارة")
                
        except Exception as e:
            print(f"❌ Error with {pair}: {e}")
        
        # هذا السطر هو Fix الـ Rate Limit
        print("⏳ استراحة 3 ثواني...")
        time.sleep(3) 
    
    if signals_sent == 0:
        print("✅ انتهى الفحص - لا توجد إشارات")
    else:
        print(f"✅ انتهى الفحص - تم إرسال {signals_sent} إشارة")

# ========== الأوامر الجديدة ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"بوت إشارات 1H V3 خدام 🔥\nالفلاتر: RSI + MACD\nالمدة: 20 دقيقة\nنراقب في: {len(PAIRS)} أزواج\n\n/status = حالة البوت\n/test = فحص فوري")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    pairs_txt = '\n'.join([f"• {p.replace('=X','').replace('XAUUSD','GOLD')}" for p in PAIRS])
    now = datetime.now(pytz.timezone('Africa/Tunis')).strftime('%H:%M:%S %d/%m')
    msg = f"""
🟢 **البوت V3 شغال**

**الوقت:** {now}
**الفحص الآلي:** كل ساعة دقيقة 01
**عدد الأزواج:** {len(PAIRS)}
**الاستراتيجية:** RSI + MACD

**الأزواج:**
{pairs_txt}

**الحماية:**
✅ UptimeRobot كل 5 دقائق
✅ Anti Rate-Limit: 3ث بين الأزواج

جرب /test للفحص اللحظي
"""
    bot.reply_to(message, msg)

@bot.message_handler(commands=['test'])
def cmd_test(message):
    bot.reply_to(message, "⏳ فحص لحظي لـ3 أزواج... استنى 15 ثانية")
    results = []
    
    for symbol in PAIRS[:3]:  # 3 أزواج فقط
        name = symbol.replace('=X', '').replace('XAUUSD', 'GOLD')
        try:
            df = yf.download(symbol, period="2d", interval="1h", progress=False, threads=False)
            if df.empty or len(df) < 30:
                results.append(f"❌ {name}: مافماش داتا")
            else:
                close = df['Close']
                # RSI
                delta = close.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = -delta.clip(upper=0).rolling(14).mean()
                rs = gain / loss
                rsi = round((100 - (100 / (1 + rs))).iloc[-1], 1)
                
                # MACD
                ema12 = close.ewm(span=12).mean()
                ema26 = close.ewm(span=26).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9).mean()
                macd_dir = "صاعد ↑" if macd.iloc[-1] > signal.iloc[-1] else "هابط ↓"
                
                results.append(f"📊 {name}\n   RSI: {rsi} | MACD: {macd_dir}")
            
            time.sleep(3)  # مهم ضد Rate Limit
        except Exception as e:
            results.append(f"❌ {name}: Error")
    
    bot.reply_to(message, "🔍 **نتيجة الفحص الفوري:**\n\n" + "\n\n".join(results) + "\n\n_الإشارة تجي كان RSI + MACD تحققو_")

def start_bot():
    tunis_tz = pytz.timezone('Africa/Tunis')
    scheduler = BackgroundScheduler(timezone=tunis_tz)
    # يخدم كل ساعة في الدقيقة 01
    scheduler.add_job(check_signals, 'cron', minute=1)
    scheduler.start()
    
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
    print("🤖 Bot V3 is running and scheduler started...")
    sys.stdout.flush()
    keep_alive()
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    start_bot()
