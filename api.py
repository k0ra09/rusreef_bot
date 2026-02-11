import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Создаем приложение
app = FastAPI()

# === НАСТРОЙКА БЕЗОПАСНОСТИ (CORS) ===
# Это "разрешение" для твоего сайта общаться с этим сервером.
# Без этого браузер заблокирует запрос.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Звездочка значит "разрешить всем". Для старта это ок.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ЧТЕНИЕ ИЗ БАЗЫ ===
@app.get("/get_history")
def get_history(user_id: int):
    """
    Функция принимает ID юзера и возвращает список его последних замеров.
    Пример запроса: /get_history?user_id=12345
    """
    # Подключаемся к базе данных (она лежит рядом на сервере)
    conn = sqlite3.connect('aquarium.db')
    cursor = conn.cursor()
    
    # Запрос SQL:
    # Выбрать дату, соленость, pH, kH
    # Из таблицы measurements
    # Где user_id совпадает с запросом
    # Сортировать: новые сверху (DESC)
    # Взять только 10 штук
    try:
        cursor.execute('''
            SELECT date, salinity, ph, kh 
            FROM measurements 
            WHERE user_id = ? 
            ORDER BY id DESC 
            LIMIT 10
        ''', (user_id,))
        
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        # Если таблицы еще нет (баг или первый запуск), вернем пустой список
        rows = []
        
    conn.close()
    
    # Сейчас данные выглядят как каша: ('2023-10-01', 35, 8.0, 7.5)
    # Превратим их в красивый словарик (JSON), который поймет сайт:
    history = []
    for row in rows:
        history.append({
            "date": row[0],
            "salinity": row[1],
            "ph": row[2],
            "kh": row[3]
        })
    
    return history