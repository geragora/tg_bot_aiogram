import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
TOKEN = '7640410337:AAFmecU5cHVValfq7Hfn_qtPjRn4NTkRdUU'#os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")
