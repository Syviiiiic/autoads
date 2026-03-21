from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = [
        [KeyboardButton("🚗 Смотреть объявления")],
        [KeyboardButton("➕ Разместить объявление")],
        [KeyboardButton("📋 Мои объявления")],
        [KeyboardButton("🔍 Поиск")],
        [KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_phone_keyboard():
    """Клавиатура для запроса телефона"""
    keyboard = [
        [KeyboardButton("📱 Отправить номер телефона", request_contact=True)],
        [KeyboardButton("◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [
        [KeyboardButton("❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_engine_type_keyboard():
    """Клавиатура для выбора типа двигателя"""
    keyboard = [
        ["Бензин", "Дизель"],
        ["Электро", "Гибрид"]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_transmission_keyboard():
    """Клавиатура для выбора КПП"""
    keyboard = [
        ["Механика", "Автомат"],
        ["Робот", "Вариатор"]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_drive_keyboard():
    """Клавиатура для выбора привода"""
    keyboard = [
        ["Передний", "Задний"],
        ["Полный"]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)