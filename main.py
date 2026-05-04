import os
import telebot
from telebot import types
from flask import Flask
import threading

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_state = {}

PAIRS = [
    'EUR/USD OTC', 'USD/JPY OTC', 'USD/CAD', 'EUR/AUD OTC', 
    'AUD/USD OTC', 'EUR/JPY OTC', 'CHF/JPY OTC', 'EUR/CHF OTC',
    'GOLD OTC', 'SILVER OTC'
]

@app.route('/')
def home():
    return "البوت خدام..."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(pair, callback_data=pair) for pair in PAIRS]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "👋 أهلا بيك في بوت إشارات زهير الذهبية 🌟\n\nاختار الزوج:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    pair = call.data
    user_state[call.from_user.id] = pair
    msg = bot.send_message(call.message.chat.id, f"📊 اخترت: {pair}\n\nاكتبلي الإشارة توا:\nمثال: 14:30 شراء 3 دقايق")
    bot.register_next_step_handler(msg, process_signal)

def process_signal(message):
    try:
        pair = user_state.get(message.from_user.id, "زوج")
        signal_text = message.text
        
        formatted_signal = f"""🌟 إشارات زهير الذهبية 🌟

📊 الزوج: {pair}
⏰ الإشارة: {signal_text}

✅ بالتوفيق للجميع"""
        
        bot.send_message(message.chat.id, formatted_signal)
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(p, callback_data=p) for p in PAIRS]
        markup.add(*buttons)
        bot.send_message(message.chat.id, "تحب تبعث إشارة أخرى؟ اختار زوج:", reply_markup=markup)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"صار Error: {e}")

def run_bot():
    print("البوت خدام...")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
