# handlers.py
import sqlite3
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from event_bot.utils import TEMP_EVENT_DATA
from event_bot.message_deletion import schedule_message_deletion


logger = logging.getLogger(__name__)

# Команда для просмотра всех событий
async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        with sqlite3.connect('events.db', timeout=10) as conn:
            c = conn.cursor()
            c.execute('SELECT id, title, date, time, description, photo_id FROM events')
            events = c.fetchall()

        if not events:
            message = await update.message.reply_text('Событий нет')
            await schedule_message_deletion(context, update.message.chat_id,
                                           [update.message.message_id, message.message_id])
            return

        response = 'Список событий:\n\n'
        for event in events:
            event_id, title, date, time, description, photo_id = event
            photo_status = '📷 Фото есть' if photo_id else '📷 Фото отсутствует'
            time_str = f'Время уведомления: {time}\n' if time else ''
            response += f'🆔 ID: {event_id}\n📅 {title}\nДата: {date}\n{time_str}Описание: {description}\n{photo_status}\n\n'

        message = await update.message.reply_text(response)
        await schedule_message_deletion(context, update.message.chat_id,
                                       [update.message.message_id, message.message_id])

    except Exception as e:
        logger.error(f"Ошибка при получении списка событий: {e}")
        message = await update.message.reply_text('Ошибка при получении списка событий')
        await schedule_message_deletion(context, update.message.chat_id,
                                       [update.message.message_id, message.message_id])

# Команда для добавления события
async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет новое событие с указанием времени уведомления."""
    try:
        # Разделяем входные данные
        args = ' '.join(context.args).split(';')
        if len(args) != 4:
            message = await update.message.reply_text('Формат: /add_event Название;ДД.ММ.ГГГГ;ЧЧ:ММ;Описание')
            context.user_data['temp_message_ids'] = [update.message.message_id, message.message_id]
            await schedule_message_deletion(
                context,
                update.message.chat_id,
                context.user_data.get('temp_message_ids', [])
            )
            return

        title, date_str, time_str, description = args

        # Проверка формата даты
        try:
            datetime.strptime(date_str, '%d.%m.%Y')
        except ValueError:
            message = await update.message.reply_text('Неверный формат даты! Используйте ДД.ММ.ГГГГ')
            context.user_data['temp_message_ids'] = [update.message.message_id, message.message_id]
            return

        # Проверка формата времени
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            message = await update.message.reply_text('Неверный формат времени! Используйте ЧЧ:ММ')
            context.user_data['temp_message_ids'] = [update.message.message_id, message.message_id]
            await schedule_message_deletion(
                context,
                update.message.chat_id,
                context.user_data.get('temp_message_ids', [])
            )
            return

        # Сохраняем временные данные и запрашиваем фото
        user_id = update.effective_user.id
        TEMP_EVENT_DATA[user_id] = {
            'title': title.strip(),
            'date': date_str,
            'time': time_str,
            'description': description.strip()
        }
        message = await update.message.reply_text('Пожалуйста, отправьте фото для события (или напишите /skip, чтобы пропустить)')
        # Сохраняем message_id команды и ответа
        context.user_data['temp_message_ids'] = [update.message.message_id, message.message_id]
        context.user_data['awaiting_photo'] = True

        logger.info(f"Состояние awaiting_photo установлено для user_id={user_id}")

    except Exception as e:
        logger.error(f"Ошибка при добавлении события: {e}")
        message = await update.message.reply_text('Ошибка при добавлении события')
        context.user_data['temp_message_ids'] = [update.message.message_id, message.message_id]
        await schedule_message_deletion(
            context,
            update.message.chat_id,
            context.user_data.get('temp_message_ids', [])
        )

# Команда для удаления события
async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет событие по ID."""
    try:
        # Проверяем, передан ли аргумент (ID события)
        if not context.args:
            message = await update.message.reply_text('Формат: /delete_event <ID события>')
            await schedule_message_deletion(
                context,
                update.message.chat_id,
                [update.message.message_id, message.message_id]
            )
            return

        event_id = context.args[0]
        # Проверяем, является ли ID числом
        try:
            event_id = int(event_id)
        except ValueError:
            message = await update.message.reply_text('ID события должно быть числом!')
            await schedule_message_deletion(
                context,
                update.message.chat_id,
                [update.message.message_id, message.message_id]
            )
            return

        with sqlite3.connect('events.db', timeout=10) as conn:
            c = conn.cursor()
            # Проверяем, существует ли событие
            c.execute('SELECT title FROM events WHERE id = ?', (event_id,))
            event = c.fetchone()

            if not event:
                message = await update.message.reply_text(f'Событие с ID {event_id} не найдено!')
                await schedule_message_deletion(
                    context,
                    update.message.chat_id,
                    [update.message.message_id, message.message_id]
                )
                return

            # Удаляем событие из таблицы events
            c.execute('DELETE FROM events WHERE id = ?', (event_id,))
            # Удаляем связанные уведомления из таблицы sent_notifications
            c.execute('DELETE FROM sent_notifications WHERE event_id = ?', (event_id,))
            conn.commit()

        message = await update.message.reply_text(f'Событие с ID {event_id} успешно удалено!')
        await schedule_message_deletion(
            context,
            update.message.chat_id,
            [update.message.message_id, message.message_id]
        )

    except Exception as e:
        logger.error(f"Ошибка при удалении события: {e}")
        message = await update.message.reply_text('Ошибка при удалении события')
        await schedule_message_deletion(
            context,
            update.message.chat_id,
            [update.message.message_id, message.message_id]
        )

# Обработчик для отправки фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает отправку фото для события."""
    user_id = update.message.from_user.id
    logger.info(
        f"Получено сообщение от user_id={user_id}, "
        f"awaiting_photo={context.user_data.get('awaiting_photo', False)}, "
        f"has_photo={bool(update.message.photo)}"
    )

    if not context.user_data.get('awaiting_photo', False):
        logger.info(f"Фото от user_id={user_id} проигнорировано, так как awaiting_photo=False")
        return

    try:
        # Проверяем, есть ли фото в сообщении
        if not update.message.photo:
            logger.warning(f"Сообщение от user_id={user_id} не содержит фото, тип сообщения: {update.message}")
            message = await update.message.reply_text('Пожалуйста, отправьте фото (изображение, а не документ).')

            context.user_data['temp_message_ids'].append(update.message.message_id)
            context.user_data['temp_message_ids'].append(message.message_id)

            return

        # Получаем фото (берём самое большое по размеру)
        photo = update.message.photo[-1]
        photo_id = photo.file_id
        logger.info(f"Получено фото с file_id={photo_id} от user_id={user_id}")

        # Получаем временные данные
        event_data = TEMP_EVENT_DATA.get(user_id)
        if not event_data:
            logger.warning(f"Данные события не найдены для user_id={user_id}")
            message = await update.message.reply_text('Ошибка: данные события не найдены.')

            context.user_data['temp_message_ids'].append(update.message.message_id)
            context.user_data['temp_message_ids'].append(message.message_id)
            context.user_data['awaiting_photo'] = False

            await schedule_message_deletion(
                context,
                update.message.chat_id,
                context.user_data.get('temp_message_ids', [])
            )
            return

        # Сохраняем событие в базу
        with sqlite3.connect('events.db', timeout=10) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO events (title, date, time, description, photo_id) VALUES (?, ?, ?, ?, ?)',
                      (event_data['title'], event_data['date'], event_data['time'], event_data['description'],
                       photo_id))
            conn.commit()

        message = await update.message.reply_text('Событие успешно добавлено!')

        context.user_data['temp_message_ids'].append(update.message.message_id)
        context.user_data['temp_message_ids'].append(message.message_id)

        logger.info(f"Событие добавлено: {event_data['title']} с photo_id={photo_id} для user_id={user_id}")

        # Планируем удаление всех сообщений, связанных с добавлением события
        await schedule_message_deletion(
            context,
            update.message.chat_id,
            context.user_data.get('temp_message_ids', [])
        )

        # Очищаем временные данные
        TEMP_EVENT_DATA.pop(user_id, None)
        context.user_data['awaiting_photo'] = False
        context.user_data['temp_message_ids'] = []

    except Exception as e:
        logger.error(f"Ошибка при сохранении фото для user_id={user_id}: {e}")
        message = await update.message.reply_text('Ошибка при сохранении фото.')

        context.user_data['temp_message_ids'].append(update.message.message_id)
        context.user_data['temp_message_ids'].append(message.message_id)

        await schedule_message_deletion(
            context,
            update.message.chat_id,
            context.user_data.get('temp_message_ids', [])
        )
        context.user_data['awaiting_photo'] = False
        TEMP_EVENT_DATA.pop(user_id, None)
        context.user_data['temp_message_ids'] = []

# Обработчик для пропуска фото
async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пропускает добавление фото для события."""
    user_id = update.message.from_user.id
    if context.user_data.get('awaiting_photo', False):
        try:
            # Получаем временные данные
            event_data = TEMP_EVENT_DATA.get(user_id)
            if not event_data:
                message = await update.message.reply_text('Ошибка: данные события не найдены.')

                context.user_data['temp_message_ids'].append(update.message.message_id)
                context.user_data['temp_message_ids'].append(message.message_id)
                context.user_data['awaiting_photo'] = False

                await schedule_message_deletion(
                    context,
                    update.message.chat_id,
                    context.user_data.get('temp_message_ids', [])
                )
                context.user_data['temp_message_ids'] = []
                return

            # Сохраняем событие в базу (без фото)
            with sqlite3.connect('events.db', timeout=10) as conn:
                c = conn.cursor()
                c.execute('INSERT INTO events (title, date, time, description, photo_id) VALUES (?, ?, ?, ?, ?)',
                          (event_data['title'], event_data['date'], event_data['time'], event_data['description'],
                           None))
                conn.commit()

            message = await update.message.reply_text('Событие успешно добавлено без фото!')

            context.user_data['temp_message_ids'].append(update.message.message_id)
            context.user_data['temp_message_ids'].append(message.message_id)

            # Планируем удаление всех сообщений, связанных с добавлением события
            await schedule_message_deletion(
                context,
                update.message.chat_id,
                context.user_data.get('temp_message_ids', [])
            )
            # Очищаем временные данные и состояние
            TEMP_EVENT_DATA.pop(user_id, None)
            context.user_data['awaiting_photo'] = False

        except Exception as e:
            logger.error(f"Ошибка при пропуске фото: {e}")
            message = await update.message.reply_text('Ошибка при добавлении события.')

            context.user_data['temp_message_ids'].append(update.message.message_id)
            context.user_data['temp_message_ids'].append(message.message_id)
            context.user_data['awaiting_photo'] = False

            TEMP_EVENT_DATA.pop(user_id, None)
            await schedule_message_deletion(
                context,
                update.message.chat_id,
                context.user_data.get('temp_message_ids', [])
            )
            context.user_data['temp_message_ids'] = []
    else:
        message = await update.message.reply_text('Сначала используйте команду /add_event!')
        await schedule_message_deletion(
            context,
            update.message.chat_id,
            [update.message.message_id, message.message_id]
        )

async def error_handler(update: Update, context):
    """Обработчик ошибок."""
    logger.error(f"Ошибка: {context.error}")
