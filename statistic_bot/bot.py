# statistics_bot/bot.py
import sqlite3
import pytz
import logging
from datetime import datetime, time
from telegram.ext import ContextTypes
from telegram import Update

from config import GROUP_CHAT_ID


logger = logging.getLogger(__name__)

# Функция для обновления счетчика сообщений и репостов пользователя
async def update_message_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Проверяем, что сообщение пришло из нужного чата
        chat_id = update.message.chat_id
        if chat_id != GROUP_CHAT_ID:
            logger.info(f"Сообщение из chat_id={chat_id} игнорируется, так как не соответствует GROUP_CHAT_ID={GROUP_CHAT_ID}")
            return

        user_id = update.message.from_user.id
        # Проверяем, является ли сообщение пересланным через forward_origin
        is_repost = hasattr(update.message, 'forward_origin') and update.message.forward_origin is not None

        # Логируем информацию о сообщении
        logger.info(f"Обработка сообщения от user_id={user_id}, is_repost={is_repost}, "
                    f"forward_origin={getattr(update.message, 'forward_origin', None)}")

        with sqlite3.connect('events.db', timeout=10) as conn:
            c = conn.cursor()
            # Проверяем, существует ли пользователь в таблице
            c.execute('SELECT message_count, repost_count FROM user_messages WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            if result:
                message_count, repost_count = result
                # Увеличиваем счетчики
                message_count += 1
                repost_count += 1 if is_repost else 0
                c.execute('UPDATE user_messages SET message_count = ?, repost_count = ? WHERE user_id = ?',
                          (message_count, repost_count, user_id))
            else:
                # Добавляем нового пользователя
                c.execute('INSERT INTO user_messages (user_id, message_count, repost_count) VALUES (?, ?, ?)',
                          (user_id, 1, 1 if is_repost else 0))
            conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при обновлении счетчика сообщений для user_id={user_id}: {e}")


# Функция для отправки ежедневной статистики и очистки данных
async def send_daily_statistics(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')
        current_date = datetime.now(ekb_tz).strftime('%d.%m.%Y')

        with sqlite3.connect('events.db', timeout=10) as conn:
            c = conn.cursor()
            # Получаем статистику сообщений и репостов
            c.execute('SELECT user_id, message_count, repost_count FROM user_messages WHERE message_count > 0')
            statistics = c.fetchall()

            if not statistics:
                message = f'📊 Статистика сообщений за {current_date}:\nНет сообщений за сегодня.'
            else:
                message = f'📊 Статистика сообщений за {current_date}:\n\n'
                for user_id, msg_count, repost_count in statistics:
                    try:
                        # Получаем имя пользователя
                        user = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
                        username = user.user.username or user.user.first_name
                        message += f'👤 {username}: {msg_count} сообщений (репостов из них: {repost_count})\n'
                    except Exception as e:
                        logger.warning(f"Не удалось получить имя пользователя {user_id}: {e}")
                        message += f'👤 ID {user_id}: {msg_count} сообщений (репостов из них: {repost_count})\n'

            # Отправляем статистику в чат
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
            logger.info(f"Отправлена статистика сообщений за {current_date}")

            # Очищаем таблицу user_messages
            c.execute('DELETE FROM user_messages')
            conn.commit()
            logger.info("Данные о сообщениях очищены после отправки статистики")

    except Exception as e:
        logger.error(f"Ошибка при отправке ежедневной статистики: {e}")

