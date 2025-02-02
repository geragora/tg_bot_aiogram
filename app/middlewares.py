import logging
from aiogram import BaseMiddleware
from aiogram.types import Message

# Создаем собственный логгер
logger = logging.getLogger(__name__)  # __name__ - это имя модуля, обеспечивает уникальность логгера.
logger.setLevel(logging.INFO)

# Создаем обработчик для вывода в консоль
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s')) # Устанавливаем формат, чтобы убрать лишнюю информацию

# Добавляем обработчик к логгеру
logger.addHandler(handler)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        logger.info(f"Получено сообщение: {event.text}")
        return await handler(event, data)
