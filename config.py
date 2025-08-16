# config.py
import logging
import os
from dotenv import load_dotenv


# Загружаем переменные из .env
load_dotenv()

# Путь к базе данных
DATABASE_PATH = 'events.db'

# Токены ботов и ID группы из .env
TOKEN = os.getenv('TELEGRAM_TOKEN')
STATS_TOKEN = os.getenv('STATS_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))

# API-ключ OpenWeatherMap, URL для запроса и город для получения погоды
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
CITY = os.getenv('CITY')
WEATHER_URL = f'http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=ru'

# Проверка наличия обязательных переменных
if not TOKEN or not STATS_TOKEN or not GROUP_CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN, STATS_TOKEN и GROUP_CHAT_ID должны быть указаны в .env файле")

# Настройка логирования
def setup_logging(bot_name='bot'):
    """Настраивает логирование с сохранением в файл logs/<bot_name>.log."""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            # Сохраняем логи в файл logs/<bot_name>.
            logging.FileHandler(f'logs/{bot_name}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)