import logging
import asyncio
from langdetect import DetectorFactory, detect
from deep_translator import GoogleTranslator


logger = logging.getLogger(__name__)

# Для стабильного определения языка
DetectorFactory.seed = 0

# Функция для определения языка и перевода
async def translate_text_if_needed(text):
    """Определяет язык текста и переводит его на русский, если требуется."""
    supported_languages = {
        'en': '🇬🇧 Английский',
        'de': '🇩🇪 Немецкий',
        'fr': '🇫🇷 Французский',
        'es': '🇪🇸 Испанский',
        'pt': '🇵🇹 Португальский',
        'it': '🇮🇹 Итальянский',
        'pl': '🇵🇱 Польский',
        'tr': '🇹🇷 Турецкий',
        'fa': '🇮🇷 Персидский',
        'ar': '🇸🇦 Арабский',
        'hi': '🇮🇳 Хинди',
        'ja': '🇯🇵 Японский',
        'zh': '🇨🇳 Китайский',
    }
    try:
        # Определяем язык текста
        lang = detect(text)
        if lang in supported_languages:
            translated = await asyncio.to_thread(GoogleTranslator(source=lang, target='ru').translate, text)
            return f"🌐 Перевод на русский (язык - {supported_languages[lang]}):\n\n {translated}"

        return None  # Если текст на русском, ничего не возвращаем

    except Exception as e:
        logger.error(f"Ошибка при переводе текста: {e}")
        return None