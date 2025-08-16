# message_deletion.py
import logging
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)

async def schedule_message_deletion(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        message_ids: list,
        delay: int = 300) -> None:
    """Планирует удаление сообщений через указанное время."""
    async def delete_messages(context: ContextTypes.DEFAULT_TYPE):
        for message_id in message_ids:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                logger.info(f"Удалено сообщение {message_id} в чате {chat_id}")
            except Exception as e:
                logger.warning(f"Ошибка при удалении сообщения {message_id} в чате {chat_id}: {e}")

    context.job_queue.run_once(delete_messages, delay, data={'message_ids': message_ids, 'chat_id': chat_id})