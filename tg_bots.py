from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
import time
import threading
from datetime import datetime, timedelta

TOKEN = "**************************************************************"
YOUR_CHAT_ID = "your_chat_id_here"  # Replace with your actual chat ID

def get_data():
    try:
        res = requests.get("http://127.0.0.1:1356/api/data")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return None

def get_total_time(data, start_time=None, end_time=None):
    if not data:
        return f"Ошибка при получении данных"
    try:
        total_sec = 0
        for entry in data:
            entry_time = entry.get("timestamp", time.time())
            if start_time and entry_time < start_time:
                continue
            if end_time and entry_time > end_time:
                continue
            total_sec += entry["duration"]
        hours = round(total_sec / 3600, 2)
        return f"Ты провёл за компом {hours} часов 💻"
    except Exception as e:
        return f"Ошибка при обработке данных: {e}"

def get_top_programs(data, start_time=None, end_time=None):
    if not data:
        return f"Ошибка при получении данных"
    try:
        program_times = {}
        for entry in data:
            entry_time = entry.get("timestamp", time.time())
            if start_time and entry_time < start_time:
                continue
            if end_time and entry_time > end_time:
                continue
            program = entry.get("program", "Unknown")
            program_times[program] = program_times.get(program, 0) + entry["duration"]
        
        # Sort programs by duration and get top 5
        sorted_programs = sorted(program_times.items(), key=lambda x: x[1], reverse=True)[:5]
        if not sorted_programs:
            return "Нет данных о программах"
        
        result = "Топ 5 программ по времени использования:\n"
        for i, (program, seconds) in enumerate(sorted_programs, 1):
            hours = round(seconds / 3600, 2)
            result += f"{i}. {program}: {hours} часов\n"
        return result
    except Exception as e:
        return f"Ошибка при обработке данных: {e}"

def start(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Общая статистика", callback_data="total"),
            InlineKeyboardButton("За сутки", callback_data="day"),
        ],
        [
            InlineKeyboardButton("За 3 дня", callback_data="3days"),
            InlineKeyboardButton("За 7 дней", callback_data="7days"),
        ],
        [
            InlineKeyboardButton("За месяц", callback_data="month"),
            InlineKeyboardButton("За всё время", callback_data="all"),
        ],
        [
            InlineKeyboardButton("Топ 5 программ", callback_data="top"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Йо! Я тебе буду слать, сколько ты сидишь за компом! Выбери статистику:", reply_markup=reply_markup)

def button(update, context):
    query = update.callback_query
    query.answer()
    
    data = get_data()
    now = time.time()
    
    if query.data == "total" or query.data == "all":
        message = get_total_time(data)
    elif query.data == "day":
        start_time = now - 24 * 3600
        message = get_total_time(data, start_time=start_time, end_time=now)
    elif query.data == "3days":
        start_time = now - 3 * 24 * 3600
        message = get_total_time(data, start_time=start_time, end_time=now)
    elif query.data == "7days":
        start_time = now - 7 * 24 * 3600
        message = get_total_time(data, start_time=start_time, end_time=now)
    elif query.data == "month":
        start_time = now - 30 * 24 * 3600
        message = get_total_time(data, start_time=start_time, end_time=now)
    elif query.data == "top":
        message = get_top_programs(data)
    else:
        message = "Неизвестная команда"
    
    query.message.reply_text(message)

def send_daily_report(context):
    while True:
        now = time.localtime()
        if now.tm_hour == 8 and now.tm_min == 0:
            data = get_data()
            message = get_total_time(data)
            context.bot.send_message(chat_id=YOUR_CHAT_ID, text=message)
        time.sleep(60)  # Check every minute

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    def error(update, context):
        print(f"Произошла ошибка: {context.error}")

    dp.add_error_handler(error)


    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    # Start the daily report in a separate thread
    threading.Thread(target=send_daily_report, args=(updater,), daemon=True).start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
