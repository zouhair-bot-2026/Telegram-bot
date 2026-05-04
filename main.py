import os
import telebot
import yfinance as yf
import pandas as pd

# توكن البوت من Render
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "تم تشغيل بوت التحليل ✅\nأرسل رمز السهم مثل: AAPL أو TSLA")

@bot.message_handler(func=lambda message: True)
def analyze_stock(message):
    try:
        ticker = message.text.strip().upper()
        bot.reply_to(message, f"لحظة نحلل في {ticker}... ⏳")
        
        # جلب البيانات
        stock = yf.Ticker(ticker)
        data = stock.history(period="6mo")
        
        if data.empty:
            bot.reply_to(message, "ما لقيتش السهم هذا ❌ تأكد من الرمز")
            return
        
        # حساب RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        last_rsi = round(rsi.iloc[-1], 2)
        
        # حساب MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        last_macd = round(macd.iloc[-1], 2)
        last_signal = round(signal.iloc[-1], 2)
        
        # السعر الحالي
        price = round(data['Close'].iloc[-1], 2)
        
        # التوصية
        if last_rsi < 30 and last_macd > last_signal:
            recommendation = "فرصة شراء قوية 💚📈"
        elif last_rsi > 70 and last_macd < last_signal:
            recommendation = "فرصة بيع / حذر 🔴📉"
        else:
            recommendation = "انتظار / حيادي 🟡"
        
        # الرد
        reply = f"""📊 تحليل {ticker}
السعر الحالي: {price}$

RSI: {last_rsi}
MACD: {last_macd}
Signal: {last_signal}

التوصية: {recommendation}
"""
        bot.reply_to(message, reply)
        
    except Exception as e:
        bot.reply_to(message, f"صار خطأ: {str(e)}")

print("Bot is running...")
bot.infinity_polling()
