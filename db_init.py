# db_init.py
import sqlite3
import logging


logger = logging.getLogger(__name__)

# Инициализация базы данных SQLite
def init_db():
    with sqlite3.connect('events.db', timeout=10) as conn:
        c = conn.cursor()

        # Таблица для событий
        c.execute('''CREATE TABLE IF NOT EXISTS events
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     title TEXT NOT NULL,
                     date TEXT NOT NULL,
                     time TEXT,
                     description TEXT,
                     photo_id TEXT)''')

        # Проверяем, есть ли столбец photo_id, и добавляем, если его нет
        c.execute("PRAGMA table_info(events)")
        columns = [info[1] for info in c.fetchall()]

        # Проверяем, есть ли столбец photo_id, и добавляем, если его нет
        if 'photo_id' not in columns:
            c.execute('ALTER TABLE events ADD COLUMN photo_id TEXT')

        # Проверяем, есть ли столбец time, и добавляем, если его нет
        if 'time' not in columns:
            c.execute('ALTER TABLE events ADD COLUMN time TEXT')

        # Таблица для отслеживания отправленных уведомлений
        c.execute('''CREATE TABLE IF NOT EXISTS sent_notifications
                     (event_id INTEGER,
                      date TEXT,
                      PRIMARY KEY (event_id, date))''')

        # Таблица для хранения количества сообщений в чате
        c.execute('''CREATE TABLE IF NOT EXISTS user_messages
                             (user_id INTEGER PRIMARY KEY,
                              message_count INTEGER DEFAULT 0,
                              repost_count INTEGER DEFAULT 0)''')
        conn.commit()
        logger.info("База данных инициализирована")