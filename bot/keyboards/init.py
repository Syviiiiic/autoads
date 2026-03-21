"""
Пакет клавиатур для бота
"""

from .reply_markups import (
    get_main_keyboard,
    get_phone_keyboard,
    get_cancel_keyboard
)

__all__ = [
    'get_main_keyboard',
    'get_phone_keyboard',
    'get_cancel_keyboard'
]