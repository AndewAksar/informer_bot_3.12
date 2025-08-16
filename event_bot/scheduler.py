# scheduler.py
import logging
import sqlite3
import pytz
from datetime import datetime
from telegram.ext import ContextTypes

from config import GROUP_CHAT_ID


logger = logging.getLogger(__name__)

# Функция для ежедневной проверки событий
async def check_events(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Текущее время
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')
        now = datetime.now(ekb_tz)
        current_date = now.strftime('%d.%m.%Y')
        current_time = now.time()
        current_datetime = now

        # # Пропускаем, если время НЕ в диапазоне с 06:00 до 23:00
        # if not (6 <= current_time.hour < 23):
        #     logger.info(f"Пропуск проверки событий, текущее время: {current_time}")
        #     return

        with sqlite3.connect('events.db', timeout=10) as conn:
            c = conn.cursor()
            # Получаем события на текущую дату
            c.execute(
                'SELECT id, title, date, time, description, photo_id FROM events WHERE date = ?',
                (current_date,)
            )
            events = c.fetchall()
            logger.info(f"Найдено событий на дату {current_date}: {len(events)}")

            for event in events:
                event_id, title, date, time_str, description, photo_id = event
                # Проверяем, было ли уже отправлено уведомление для этого события сегодня
                c.execute('SELECT COUNT(*) FROM sent_notifications WHERE event_id = ? AND date = ?',
                          (event_id, current_date))
                already_sent = c.fetchone()[0] > 0
                logger.info(f"Событие ID={event_id}, already_sent={already_sent}")

                if not already_sent:
                    # Определяем время отправки уведомления
                    notification_time = time_str if time_str else '10:00'
                    try:
                        notification_datetime = datetime.strptime(f"{date} {notification_time}", '%d.%m.%Y %H:%M')
                        notification_datetime = ekb_tz.localize(notification_datetime)
                        time_diff = (current_datetime - notification_datetime).total_seconds() / 60

                        if -1 <= time_diff <= 1:  # Окно ±1 минуту
                            # Формируем сообщение и обрезаем его до 1024 символов, чтобы оставить запас
                            message = f'📅 Сегодняшнее событие!\n\nНазвание: {title}\nДата: {date}\nВремя уведомления: {notification_time}\nОписание: {description}'
                            if len(message) > 1024:
                                message = message[:1024] + '...'
                                logger.warning(f"Подпись к событию {event_id} обрезана до 1024 символов")


                            # Отправляем уведомление с фото, если оно есть
                            logger.info(f"Отправка уведомления для события ID={event_id}, title={title}")
                            if photo_id:
                                await context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo_id, caption=message)
                            else:
                                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)

                            logger.info(f"Отправлено уведомление о событии: {title} (ID: {event_id})")

                            # Сохраняем информацию об отправленном уведомлении
                            try:
                                c.execute('INSERT INTO sent_notifications (event_id, date) VALUES (?, ?)',
                                          (event_id, current_date))
                                conn.commit()
                            except sqlite3.IntegrityError as e:
                                logger.warning("Попытка повторной вставки уведомления для event_id={event_id}, date={current_date}: {e}")
                                continue

                    except ValueError as e:
                        logger.error(f"Ошибка при разборе времени события {event_id}: {e}")
                        continue

    except Exception as e:
        logger.error(f"Ошибка при проверке событий: {e}")
