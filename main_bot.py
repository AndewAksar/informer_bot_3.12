# main_bot.py
import pytz
import asyncio
from datetime import datetime, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext.filters import ALL, COMMAND

from config import TOKEN, STATS_TOKEN, setup_logging
from db_init import init_db
from voice_bot.handlers import handle_voice
from translator_bot.handlers import handle_text
from weather_bot.handlers import send_weather_report
from event_bot.handlers import *
from event_bot.scheduler import check_events
from event_bot.utils import AwaitingPhotoFilter
from event_bot.commands import info


logger = setup_logging('main_bot')

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ошибки бота."""
    error = context.error
    logger.error(f"Ошибка: {context.error}")
    if "Conflict" in str(error):
        logger.error(f"Конфликт getUpdates. Убедитесь, что только один экземпляр бота запущен. "
                     f"Попробуйте удалить вебхук: curl https://api.telegram.org/bot{context.bot.token}/deleteWebhook")

# Главная функция
def main() -> None:
    """Запускает главный бот (основной функционал)."""
    try:
        # Инициализация базы данных
        logger.info("Инициализация базы данных")
        init_db()

        # Создаем приложение и добавляем обработчик ошибок
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_error_handler(error_handler)

        # Добавляем специфические обработчики (voice_bot, event_bot, translator_bot)
        app.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice, block=False))
        app.add_handler(MessageHandler(filters.PHOTO & AwaitingPhotoFilter(), handle_photo, block=False))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text, block=False))

        # Добавляем обработчик команд (event_bot)
        app.add_handler(CommandHandler('info', info))
        app.add_handler(CommandHandler('add_event', add_event))
        app.add_handler(CommandHandler('list_events', list_events))
        app.add_handler(CommandHandler('delete_event', delete_event))
        app.add_handler(CommandHandler('skip', skip_photo))

        # Установка таймзоны
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')

        # Добавляем задачу для ежедневной проверки событий (event_bot)
        app.job_queue.run_repeating(check_events, interval=60, first=0)

        # Добавляем задачу для отправки погоды в 11:00 по уральскому времени (weather_bot)
        app.job_queue.run_daily(
            send_weather_report,
            time=time(hour=11, minute=0, tzinfo=ekb_tz),  # Используем time вместо datetime.time
            days=(0, 1, 2, 3, 4, 5, 6)
        )

        # Запуск main бота
        logger.info("Основной бот запущен")
        app.run_polling(drop_pending_updates=True, close_loop=False)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

# Запуск бота
if __name__ == '__main__':
    main()
