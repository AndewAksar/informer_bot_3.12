# add_main_bot.py
import pytz
from datetime import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.ext.filters import ALL, COMMAND

from config import STATS_TOKEN, GROUP_CHAT_ID, setup_logging
from db_init import init_db
from statistic_bot.bot import update_message_count, send_daily_statistics


logger = setup_logging('stats_bot')

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ошибки бота."""
    logger.error(f"Ошибка в боте с токеном {context.bot.token}: {context.error}")
    if "Conflict" in str(context.error):
        logger.error(f"Конфликт getUpdates. Убедитесь, что только один экземпляр бота запущен. "
                     f"Попробуйте удалить вебхук: curl https://api.telegram.org/bot{context.bot.token}/deleteWebhook")

def main() -> None:
    """Запускает второй бот (статистика)."""
    try:
        # Инициализация базы данных (если не существует, и если Docker выполнит вызов данного бота первым)
        logger.info("Инициализация базы данных")
        init_db()

        # Создаем приложение и добавляем обработчик ошибок
        app = ApplicationBuilder().token(STATS_TOKEN).build()
        app.add_error_handler(error_handler)

        # Обработчики
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, update_message_count, block=False))

        # Установка таймзоны
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')

        # Запуск задач в определенные часы (22:00 по уральскому времени)
        app.job_queue.run_daily(
            send_daily_statistics,
            time=time(hour=22, minute=0, tzinfo=ekb_tz),
            days=(0, 1, 2, 3, 4, 5, 6)
        )

        # Запуск бота
        logger.info("Запуск второго бота (статистика)")
        app.run_polling(drop_pending_updates=True, close_loop=False)

    except Exception as e:
        logger.error(f"Ошибка при запуске второго бота: {e}")
        raise

if __name__ == '__main__':
    main()