import logging
from telegram.ext import ContextTypes

from weather_bot.utils import get_weather
from config import GROUP_CHAT_ID


logger = logging.getLogger(__name__)

# Функция для отправки отчета о погоде
async def send_weather_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Вызвана функция send_weather_report")
    try:
        weather_report = get_weather()
        logger.info(f"Получены данные о погоде: {weather_report}")
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=weather_report)
        logger.info("Отчет о погоде отправлен")
    except Exception as e:
        logger.error(f"Ошибка при отправке отчета о погоде: {e}")