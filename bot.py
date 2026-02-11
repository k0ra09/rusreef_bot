import asyncio
import json
import sqlite3
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = "https://k0ra09.github.io/rusreef_bot/webapp/index.html"

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================

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


def get_last_measurements(user_id, limit=5):
    conn = sqlite3.connect("aquarium.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, salinity, ph, kh
        FROM measurements
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return rows

# ================= HANDLERS =================

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

    await message.answer("🌊 RusReef готов к работе.", reply_markup=keyboard)


@dp.message(F.web_app_data)
async def handle_webapp(message: types.Message):
    data = json.loads(message.web_app_data.data)

    try:
        salinity = float(data["salinity"]) if data["salinity"] else 0
        ph = float(data["ph"]) if data["ph"] else 0
        kh = float(data["kh"]) if data["kh"] else 0
    except ValueError:
        await message.answer("❌ Введены некорректные числа.")
        return

    warnings = []

    if salinity and not (34 <= salinity <= 36):
        warnings.append("⚠️ Соленость вне нормы (34–36 ppt)")

    if ph and not (7.8 <= ph <= 8.5):
        warnings.append("⚠️ pH вне нормы (7.8–8.5)")

    if kh and not (6 <= kh <= 12):
        warnings.append("⚠️ kH вне нормы (6–12 dKH)")

    save_measurement(message.from_user.id, salinity, ph, kh)

    response = (
        f"✅ Замер сохранён!\n\n"
        f"🧂 Соль: {salinity}\n"
        f"🧪 pH: {ph}\n"
        f"💎 kH: {kh}"
    )

    if warnings:
        response += "\n\n" + "\n".join(warnings)

    await message.answer(response)


@dp.message(F.text == "📊 История")
async def history(message: types.Message):
    rows = get_last_measurements(message.from_user.id)

    if not rows:
        await message.answer("📭 История пока пуста.")
        return

    text = "📊 Последние замеры:\n\n"

    for row in rows:
        date, salinity, ph, kh = row

        def check(value, low, high):
            if low <= value <= high:
                return f"🟢 {value}"
            else:
                return f"🔴 {value}"

        text += (
            f"📅 {date}\n"
            f"🧂 {check(salinity, 34, 36)} | "
            f"🧪 {check(ph, 7.8, 8.5)} | "
            f"💎 {check(kh, 6, 12)}\n"
            f"──────────────\n"
        )

    await message.answer(text)

# ================= RUN =================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())