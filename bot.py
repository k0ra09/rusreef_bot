import asyncio
import json
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo

TOKEN = "8595417826:AAH4bCiGjFZrt1pZ8Kdrw57C4G5Gd1Vy9hE"
WEBAPP_URL = "https://k0ra09.github.io/rusreef_bot/webapp/index.html"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ---------- БАЗА ДАННЫХ ----------

def init_db():
    conn = sqlite3.connect("aquarium.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            salinity REAL,
            ph REAL,
            kh REAL
        )
    """)

    conn.commit()
    conn.close()


def save_measurement(user_id, salinity, ph, kh):
    conn = sqlite3.connect("aquarium.db")
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO measurements (user_id, date, salinity, ph, kh)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, now, salinity, ph, kh))

    conn.commit()
    conn.close()


# ---------- ОБРАБОТЧИКИ ----------

@dp.message(Command("start"))
async def start(message: types.Message):
    init_db()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text="📝 Внести замеры",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )],
            [types.KeyboardButton(text="📊 История")]
        ],
        resize_keyboard=True
    )

    await message.answer("RusReef запущен 🌊", reply_markup=keyboard)


@dp.message(F.web_app_data)
async def handle_webapp(message: types.Message):
    data = json.loads(message.web_app_data.data)

    salinity = float(data["salinity"]) if data["salinity"] else 0
    ph = float(data["ph"]) if data["ph"] else 0
    kh = float(data["kh"]) if data["kh"] else 0

    save_measurement(message.from_user.id, salinity, ph, kh)

    await message.answer("✅ Сохранено!")


@dp.message(F.text == "📊 История")
async def history(message: types.Message):
    conn = sqlite3.connect("aquarium.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, salinity, ph, kh
        FROM measurements
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (message.from_user.id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("История пуста.")
        return

    text = "📊 Последние замеры:\n\n"
    for row in rows:
        text += f"{row[0]}\n🧂 {row[1]} | 🧪 {row[2]} | 💎 {row[3]}\n\n"

    await message.answer(text)


# ---------- ЗАПУСК ----------

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())    return history