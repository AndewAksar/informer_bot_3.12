import logging
from telegram import Update
from telegram.ext import ContextTypes

from translator_bot.utils import translate_text_if_needed
from config import GROUP_CHAT_ID


logger = logging.getLogger(__name__)

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения в указанной группе и переводит их."""
    chat_id = update.message.chat_id
    if chat_id != GROUP_CHAT_ID:
        logger.info(f"Сообщение проигнорировано: чат {chat_id} не совпадает с GROUP_CHAT_ID {GROUP_CHAT_ID}")
        return  # Игнорируем сообщения из других чатов

    text = update.message.text
    translation = await translate_text_if_needed(text)
    if translation:
        await update.message.reply_text(translation)
        logger.info(f"Переведено сообщение в чате {chat_id}: {translation}")