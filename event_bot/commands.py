# commands.py
import logging
from telegram import Update
from telegram.ext import ContextTypes

from event_bot.message_deletion import schedule_message_deletion


logger = logging.getLogger(__name__)

# Команда /start
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    chat_id = update.message.chat_id
    message = await update.message.reply_text(
        "✨ **Добро пожаловать!** ✨\n"
        "Я - бот для информирования о событиях! 🔔\n\n"
        "**📋 Доступные команды:**\n\n"
        "• Добавить событие с временем уведомления:\n"
        "`/add_event <название>;<дата ДД.ММ.ГГГГ>;<ЧЧ:ММ>;<описание>`\n\n"
        "Пример:\n"
        "```\n"
        "/add_event Встреча;15.08.2025;14:30;Обсуждение планов\n"
        "```\n"
        "• Показать список всех событий:\n"
        "`/list_events`\n\n"
        "• Удалить событие по его ID:\n"
        "`/delete_event <ID события>`\n\n"
        "**⚠️ Важно:**\n"
        "Описание не должно превышать 1024 символа.\n"
        "Время уведомления указывайте в формате ЧЧ:ММ (например, 09:00 или 14:30).",
        parse_mode="Markdown"
    )
    logger.info(f"Команда /info вызвана в чате {chat_id}")

    # Планируем удаление сообщений команды /start и ответа бота через 5 минут
    await schedule_message_deletion(context, chat_id, [update.message.message_id, message.message_id])