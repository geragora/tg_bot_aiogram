import logging
from aiogram import BaseMiddleware
from aiogram.types import Message

# Настройка логирования
logging.basicConfig(
    filename="bot_logs.log",  # Имя файла для логов
    level=logging.INFO,  # Уровень логирования
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат сообщений
)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        # Логирование полученного сообщения
        logging.info(f"Получено сообщение: {event.text}")
        return await handler(event, data)
