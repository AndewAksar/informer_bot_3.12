# handlers.py
import logging
import random
import os
from telegram import Update
from telegram.ext import ContextTypes

from voice_bot.utils import download_voice, recognize_speech
from config import GROUP_CHAT_ID


logger = logging.getLogger(__name__)

# Функция для экранирования специальных символов в MarkdownV2
def escape_markdown_v2(text: str) -> str:
    """Экранирует специальные символы для MarkdownV2."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Обработчик голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает голосовые сообщения только в указанной группе и распознает их."""
    chat_id = update.message.chat_id
    logger.info(f"Получено голосовое сообщение в чате {chat_id}")

    try:
        if chat_id == GROUP_CHAT_ID:
            voice = update.message.voice
            if voice:
                # Генерируем уникальное имя файла
                file_path = f"voice_{random.randint(1000, 9999)}"

                # Скачиваем голосовое сообщение
                ogg_file = await download_voice(voice, file_path)

                if ogg_file:
                    # Распознаем речь
                    text = await recognize_speech(ogg_file)

                    # Экранируем текст для MarkdownV2
                    escaped_text = escape_markdown_v2(text)

                    # Отправляем расшифрованный текст
                    await update.message.reply_text(f'> {escaped_text}', parse_mode='MarkdownV2')

                    # Удаляем временный OGG файл
                    if os.path.exists(ogg_file):
                        os.remove(ogg_file)
                        logger.info(f"Файл {ogg_file} удален")
                    logger.info(f"Бот ответил на голосовое сообщение в чате {chat_id} с текстом: {text}")
                else:
                    await update.message.reply_text('Не удалось обработать голосовое сообщение.')
                    logger.error(f"Не удалось обработать голосовое сообщение в чате {chat_id}")
            else:
                logger.info(f"Сообщение не является голосовым в чате {chat_id}")
        else:
            logger.info(f"Голосовое сообщение проигнорировано: чат {chat_id} не совпадает с GROUP_CHAT_ID {GROUP_CHAT_ID}")
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения в чате {chat_id}: {e}")
        await update.message.reply_text('Произошла ошибка при обработке голосового сообщения.')
