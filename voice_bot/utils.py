# utils.py
import logging
import os
import random
import speech_recognition as sr
from pydub import AudioSegment


logger = logging.getLogger(__name__)
recognizer = sr.Recognizer()

# Функция для скачивания голосового сообщения
async  def download_voice(voice_file, file_path: str) -> str:
    """Скачивает голосовое сообщение в формате OGG."""
    try:
        file = await voice_file.get_file()
        file_data = await file.download_as_bytearray()
        with open(file_path + '.ogg', 'wb') as f:
            f.write(file_data)
        return file_path + '.ogg'
    except Exception as e:
        logger.error(f"Ошибка при скачивании голосового сообщения: {e}")
        return None

# Функция для распознавания речи
async def recognize_speech(file_path: str) -> str:
    """Распознает речь из OGG файла."""
    try:
        # Конвертируем OGG в WAV
        audio = AudioSegment.from_ogg(file_path)
        wav_path = file_path.replace('.ogg', '.wav')
        audio.export(wav_path, format='wav')

        # Распознаем речь
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language='ru-RU')
            os.remove(wav_path)  # Удаляем временный WAV файл
            return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь."
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания: {e}"
    except Exception as e:
        logger.error(f"Ошибка при распознавании речи: {e}")
        return "Произошла ошибка при обработке аудио."