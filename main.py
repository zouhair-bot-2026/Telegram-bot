import os
import time
import asyncio
import yfinance as yf
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, time as dt_time
from flask import Flask
from threading import Thread

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

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

app = Flask(__name__)

@app.route('/')
def home():
    return "بوت الفوركس شغال 24/7 ✅"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_sma(data, period):
    return data.rolling(window=period).mean()

def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def get_trend(ema9, ema21):
    if ema9 > ema21:
        return "صاعد 📈"
    elif ema9 < ema21:
        return "هابط 📉"
    else:
        return "عرضي ➡️"

def get_support_resistance(data):
    try:
        recent_high = data['High'].tail(50).max()
        recent_low = data['Low'].tail(50).min()
        return recent_high, recent_low
    except:
        return None, None

def analyze_pair(pair_name):
    try:
        symbol = PAIRS[pair_name]
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        
        if len(data) < 200:
            print(f"{pair_name}: داتا ناقصة")
            return None
            
        close = data['Close']
        high = data['High']
        low = data['Low']
        
        sma200 = calculate_sma(close, 200).iloc[-1]
        ema9 = calculate_ema(close, 9).iloc[-1]
        ema21 = calculate_ema(close, 21).iloc[-1]
        rsi = calculate_rsi(close, 14).iloc[-1]
        
        current_price = close.iloc[-1]
        prev_price = close.iloc[-2]
        trend = get_trend(ema9, ema21)
        resistance, support = get_support_resistance(data)
        
        signal = None
        reason = ""
        
        if (current_price < sma200 and 
            ema9 < ema21 and 
            rsi > 50 and rsi < 70 and
            current_price < prev_price):
            signal = "🔴 إشارة بيع"
            reason = "السعر تحت SMA200 + ترند هابط + RSI مناسب"
            
        elif (current_price > sma200 and 
              ema9 > ema21 and 
              rsi < 50 and rsi > 30 and
              current_price > prev_price):
            signal = "🟢 إشارة شراء"
            reason = "السعر فوق SMA200 + ترند صاعد + RSI مناسب"
        
        if signal:
            msg = f"{signal} {pair_name}\n\n"
            msg += f"💰 السعر الحالي: {current_price:.5f}\n"
            msg += f"📊 الترند: {trend}\n"
            msg += f"📈 RSI: {rsi:.2f}\n"
            msg += f"📉 SMA200: {sma200:.5f}\n"
            msg += f"⚡ EMA9: {ema9:.5f}\n"
            msg += f"⚡ EMA21: {ema21:.5f}\n"
            if support and resistance:
                msg += f"🛡️ الدعم: {support:.5f}\n"
                msg += f"🚧 المقاومة: {resistance:.5f}\n"
            msg += f"\n💡 السبب: {reason}\n"
            msg += f"⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}"
            return msg
        return None
        
    except Exception as e:
        print(f"Error analyzing {pair_name}: {e}")
        return None

async def send_signals(context: ContextTypes.DEFAULT_TYPE):
    print(f"🔍 جاري فحص الإشارات... {datetime.now()}")
    signals_found = 0
    
    for pair in PAIRS.keys():
        try:
            msg = analyze_pair(pair)
            if msg:
                await context.bot.send_message(chat_id=CHAT_ID, text=msg)
                signals_found += 1
                print(f"✅ تم إرسال إشارة {pair}")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ خطأ في إرسال {pair}: {e}")
    
    if signals_found == 0:
        print("📭 لا توجد إشارات هذه الساعة")
    else:
        print(f"📤 تم إرسال {signals_found} إشارات")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 جاري الفحص الفوري لكل الأزواج...")
    signals_found = 0
    
    for pair in PAIRS.keys():
        try:
            msg = analyze_pair(pair)
            if msg:
                await update.message.reply_text(msg)
                signals_found += 1
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error in test {pair}: {e}")
    
    if signals_found == 0:
        await update.message.reply_text("❌ لا توجد إشارات حاليا حسب الاستراتيجية\n\nالاستراتيجية تتطلب:\n1- شراء: فوق SMA200 + ترند صاعد + RSI 30-50\n2- بيع: تحت SMA200 + ترند هابط + RSI 50-70")
    else:
        await update.message.reply_text(f"✅ انتهى الفحص\n📊 عدد الإشارات: {signals_found}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = "🤖 أهلا بيك في بوت إشارات الفوركس\n\n"
    welcome_msg += "✅ البوت شغال 24/7 على السيرفر\n"
    welcome_msg += "📈 يراقب 10 أزواج رئيسية:\n"
    welcome_msg += "EURUSD, GBPUSD, USDJPY, EURCHF, AUDUSD\n"
    welcome_msg += "USDCAD, NZDUSD, EURGBP, USDCHF, EURJPY\n\n"
    welcome_msg += "⏰ يفحص الإشارات كل 30 دقيقة\n"
    welcome_msg += "📊 ملخص يومي الساعة 22:00 بتوقيت تونس\n\n"
    welcome_msg += "🎯 الأوامر المتاحة:\n"
    welcome_msg += "/test - فحص فوري لكل الأزواج\n"
    welcome_msg += "/start - عرض هذه الرسالة\n\n"
    welcome_msg += "بالتوفيق 💚"
    await update.message.reply_text(welcome_msg)

async def daily_summary(context: ContextTypes.DEFAULT_TYPE):
    summary = f"📊 الملخص اليومي {datetime.now().strftime('%d/%m/%Y')}\n\n"
    summary += "✅ البوت اشتغل 24 ساعة بدون توقف\n"
    summary += "📈 يراقب 10 أزواج فوركس\n"
    summary += "⏰ فحص الإشارات كل 30 دقيقة\n"
    summary += "🔍 استراتيجية: SMA200 + EMA9/21 + RSI\n\n"
    summary += "💡 نصيحة: إدارة رأس المال أهم من الإشارة\n"
    summary += "غدوة يوم جديد و فرص جديدة 💪"
    await context.bot.send_message(chat_id=CHAT_ID, text=summary)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("test", test_command))
    
    job_queue = application.job_queue
    job_queue.run_repeating(send_signals, interval=1800, first=10)
    job_queue.run_daily(daily_summary, time=dt_time(hour=20, minute=0))
    
    print("🚀 البوت بدأ بنجاح...")
    application.run_polling()

if __name__ == '__main__':
    Thread(target=run_flask, daemon=True).start()
    main()
