import asyncio
import logging
import json # <--- Добавили библиотеку для работы с JSON
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo

# === КОНФИГУРАЦИЯ ===
TOKEN = "8595417826:AAH4bCiGjFZrt1pZ8Kdrw57C4G5Gd1Vy9hE" 
WEBAPP_URL = "https://k0ra09.github.io/rusreef_bot/webapp/index.html"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# === ОБРАБОТЧИКИ ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📝 Внести замеры", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True
    )
    await message.answer("Привет! Нажми кнопку, чтобы внести параметры воды.", reply_markup=keyboard)

# НОВЫЙ ХЕНДЛЕР: Ловит данные из WebApp
@dp.message(F.web_app_data) # Срабатывает, когда прилетают данные из веб-аппа
async def web_app_data_handler(message: types.Message):
    # Получаем данные (они приходят как строка)
    raw_data = message.web_app_data.data
    
    # Превращаем строку обратно в словарь Python
    data = json.loads(raw_data)
    
    # Формируем ответ
    text_response = (
        f"✅ Данные получены!\n\n"
        f"🧂 Соленость: {data['salinity']}\n"
        f"🧪 pH: {data['ph']}\n"
        f"💎 kH: {data['kh']}"
    )
    
    # Отправляем подтверждение пользователю
    await message.answer(text_response)

# === ЗАПУСК ===
async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")