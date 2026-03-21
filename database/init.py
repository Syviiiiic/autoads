"""
Пакет для работы с базой данных
"""

from .models import User, Ad, Favorite
from .queries import UserQueries, AdQueries
from .db import get_db, init_db

__all__ = [
    'User', 'Ad', 'Favorite',
    'UserQueries', 'AdQueries',
    'get_db', 'init_db'
]