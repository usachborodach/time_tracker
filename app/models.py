import logging
from datetime import datetime

from flask_login import UserMixin

from .extensions import get_db

logger = logging.getLogger(__name__)


# Часы, которые будут отображаться
HOURS = [
    '07:00', '08:00', '09:00', '10:00', '11:00', '12:00',
    '13:00', '14:00', '15:00', '16:00', '17:00',
    '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
]

# Список доступных активностей
ACTIVITIES = [
    'Обзор задач',
    'Работал',
    'Учился',
    'Кодил для себя',
    'Домашние задачи',
    'Банджо',
    'Залипал',
    'Спал',
    'Время с семьёй',
    'Время с Юлочкой',
    'Время с Ваней',
    'Время с Таней',
]


class User(UserMixin):
    def __init__(self, username: str):
        self.id = username


def days_collection():
    return get_db().days


def get_or_create_day(date_obj):
    """Возвращает документ дня, создавая его при отсутствии."""
    date_datetime = datetime(date_obj.year, date_obj.month, date_obj.day)
    doc = days_collection().find_one({'date': date_datetime})
    if doc is None:
        doc = {
            'date': date_datetime,
            'hours': {hour: '' for hour in HOURS},
        }
        days_collection().insert_one(doc)
        logger.info("Created new day record for %s", date_obj)
    return doc


def update_day_hour(date_obj, hour: str, activity: str) -> bool:
    if hour not in HOURS:
        raise ValueError(f"Unknown hour: {hour}")

    date_datetime = datetime(date_obj.year, date_obj.month, date_obj.day)
    result = days_collection().update_one(
        {'date': date_datetime},
        {'$set': {f'hours.{hour}': activity}},
    )
    if result.matched_count == 0:
        get_or_create_day(date_obj)
        days_collection().update_one(
            {'date': date_datetime},
            {'$set': {f'hours.{hour}': activity}},
        )
    return True