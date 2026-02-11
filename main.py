import asyncio
import logging
import json
import sqlite3  # <--- Добавили модуль для работы с базой данных
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo

# === КОНФИГУРАЦИЯ ===
TOKEN = "8595417826:AAH4bCiGjFZrt1pZ8Kdrw57C4G5Gd1Vy9hE"
WEBAPP_URL = "https://k0ra09.github.io/rusreef_bot/webapp/index.html" # Проверь, верная ли ссылка

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# === РАБОТА С БАЗОЙ ДАННЫХ ===

def init_db():
    """
    Создает файл базы данных и таблицу, если их нет.
    """
    # Подключаемся к файлу (если его нет, он создастся сам)
    conn = sqlite3.connect('aquarium.db')
    cursor = conn.cursor()
    
    # Создаем таблицу measurements (измерения)
    # id - уникальный номер записи
    # date - дата и время
    # salinity, ph, kh - наши параметры
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            salinity REAL,
            ph REAL,
            kh REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_measurement(user_id, salinity, ph, kh):
    """
    Сохраняет конкретные цифры в базу.
    """
    conn = sqlite3.connect('aquarium.db')
    cursor = conn.cursor()
    
    # Получаем текущее время
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Записываем (INSERT) данные
    cursor.execute('''
        INSERT INTO measurements (user_id, date, salinity, ph, kh)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, current_time, salinity, ph, kh))
    
    conn.commit()
    conn.close()

# === ОБРАБОТЧИКИ (HANDLERS) ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Запускаем создание базы при старте, на всякий случай
    init_db()
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📝 Внести замеры", web_app=WebAppInfo(url=WEBAPP_URL))],
            [types.KeyboardButton(text="📊 История (последние 5)")] # Добавили кнопку для проверки
        ],
        resize_keyboard=True
    )
    await message.answer("Привет! База данных готова к работе.", reply_markup=keyboard)

# Ловит данные из WebApp и СОХРАНЯЕТ их
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    raw_data = message.web_app_data.data
    data = json.loads(raw_data)
    
    # 1. Сохраняем в базу
    # float() превращает текст "35" в число 35.0, чтобы база понимала, что это цифры
    try:
        salinity = float(data['salinity']) if data['salinity'] else 0.0
        ph = float(data['ph']) if data['ph'] else 0.0
        kh = float(data['kh']) if data['kh'] else 0.0
        
        save_measurement(message.from_user.id, salinity, ph, kh)
        
        await message.answer(f"✅ Данные сохранены в базу!\nСоль: {salinity}, pH: {ph}, kH: {kh}")
        
    except ValueError:
        await message.answer("❌ Ошибка: введены некорректные числа.")

# Простая кнопка посмотреть историю, чтобы убедиться, что сохраняется
@dp.message(F.text == "📊 История (последние 5)")
async def show_history(message: types.Message):
    conn = sqlite3.connect('aquarium.db')
    cursor = conn.cursor()
    
    # Берем последние 5 записей, отсортированных по id (сначала новые)
    cursor.execute('SELECT date, salinity, ph, kh FROM measurements WHERE user_id = ? ORDER BY id DESC LIMIT 5', (message.from_user.id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await message.answer("История пуста.")
        return

    response = "📋 **Последние замеры:**\n\n"
    for row in rows:
        # row[0] это дата, row[1] соль и т.д.
        response += f"📅 {row[0]}\n🧂 {row[1]} | 🧪 {row[2]} | 💎 {row[3]}\n➖➖➖➖➖➖\n"
        
    await message.answer(response)

# === ЗАПУСК ===
async def main():
    # Создаем таблицу сразу при запуске бота
    init_db()
    print("База данных проверена/создана.")
    print("Бот запущен...")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен") 