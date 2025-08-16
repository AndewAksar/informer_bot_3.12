# utils.py
import logging
from telegram.ext import filters
from telegram import Update


logger = logging.getLogger(__name__)

# Словарь для хранения временных данных о событии
TEMP_EVENT_DATA = {}

class AwaitingPhotoFilter(filters.BaseFilter):
    """Фильтр для проверки состояния awaiting_photo."""
    def filter(self, update):
        if not (update.effective_user and update.message):
            return False
        # Проверяем context.user_data для текущего пользователя
        is_awaiting = update.get_bot().application.user_data.get(update.effective_user.id, {}).get('awaiting_photo', False)
        logger.info(f"AwaitingPhotoFilter: user_id={update.effective_user.id}, awaiting_photo={is_awaiting}")
        return is_awaiting