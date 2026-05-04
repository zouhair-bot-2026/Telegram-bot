
import telebot
from telebot import types
import threading
from flask import Flask

# التوكن متاعك - حطو في Render كـ Environment Variable اسمو TOKEN
import os
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Flask باش Render ما يطيحش البوت
app = Flask(__name__)

@app.route('/')
def home():
    return "إشارات زهير الذهبية خدام 🔥"

# الأزواج اللي طلبتهم
pairs = [
    "EUR/USD OTC", "USD/JPY OTC", "USD/CAD", "EUR/AUD OTC", 
    "AUD/USD OTC", "EUR/JPY OTC", "CHF/JPY OTC", 
    "EUR/CHF OTC", "GOLD OTC", "SILVER OTC"
]

# امر /start
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(pair) for pair in pairs]
    markup.add(*buttons)
    
    bot.reply_to(message, 
        f"مرحبا بك في *إشارات زهير الذهبية* 🌟\n\n"
        f"اختر الزوج اللي تحب تاخذ عليه إشارة:",
        parse_mode='Markdown',
        reply_markup=markup)

# كي تضغط على اي زوج
@bot.message_handler(func=lambda message: message.text in pairs)
def send_signal(message):
    pair = message.text
    msg = bot.reply_to(message, f"اكتب إ
