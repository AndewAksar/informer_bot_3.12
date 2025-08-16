import requests
import logging
import pytz
from datetime import datetime

from config import CITY, WEATHER_URL


logger = logging.getLogger(__name__)

# Функция для преобразования кода иконки в эмодзи
def get_weather_emoji(icon):
    icon_to_emoji = {
        '01d': '☀️', '01n': '🌙',  # Ясно
        '02d': '⛅', '02n': '⛅',  # Малооблачно
        '03d': '☁️', '03n': '☁️',  # Облачно
        '04d': '☁️', '04n': '☁️',  # Полная облачность
        '09d': '🌧️', '09n': '🌧️',  # Дождь
        '10d': '🌦️', '10n': '🌦️',  # Небольшой дождь
        '11d': '⛈️', '11n': '⛈️',  # Гроза
        '13d': '❄️', '13n': '❄️',  # Снег
        '50d': '🌫️', '50n': '🌫️'   # Туман
    }
    return icon_to_emoji.get(icon, '🌡️')  # По умолчанию

# Функция для получения данных о погоде
def get_weather():
    try:
        # Получаем данные о погоде
        response = requests.get(WEATHER_URL)
        response.raise_for_status()  # Проверяем успешность запроса
        data = response.json()

        # Извлекаем данные о погоде
        emoji = get_weather_emoji(data['weather'][0]['icon'])
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        pressure = data['main']['pressure']     # Давление в гПа
        visibility = data['visibility'] / 1000  # Видимость в километрах
        cloudiness = data['clouds']['all']      # Облачность в процентах

        # Восход и закат солнца (переводим из Unix timestamp в локальное время Екатеринбурга)
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')
        sunrise = datetime.fromtimestamp(data['sys']['sunrise'], tz=ekb_tz).strftime('%H:%M')
        sunset = datetime.fromtimestamp(data['sys']['sunset'], tz=ekb_tz).strftime('%H:%M')

        # Формируем сообщение
        return (f'🌤️ Погода в {CITY} на сегодня:\n'
                f'Температура: {temp}°C\n'
                f'Ощущается как: {feels_like}°C\n'
                f'Погода: {description} {emoji}\n'
                f'Влажность: {humidity}%\n'
                f'Скорость ветра: {wind_speed} м/с\n'
                f'Давление: {pressure} гПа\n'
                f'Видимость: {visibility} км\n'
                f'Облачность: {cloudiness}%\n'
                f'Восход солнца: {sunrise}\n'
                f'Закат солнца: {sunset}')
    except Exception as e:
        logger.error(f'Ошибка получения данных о погоде: {e}')
        return "Не удалось получить данные о погоде"