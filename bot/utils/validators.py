import re
from datetime import datetime

def validate_year(year_text: str):
    """Проверка года выпуска"""
    try:
        year = int(year_text)
        current_year = datetime.now().year
        
        if year < 1900 or year > current_year + 1:
            return False, f"Год должен быть от 1900 до {current_year + 1}"
        
        return True, year
    except ValueError:
        return False, "Введите корректный год (только цифры)"

def validate_price(price_text: str):
    """Проверка цены"""
    # Убираем пробелы и другие разделители
    price_text = re.sub(r'[^\d]', '', price_text)
    
    try:
        price = int(price_text)
        
        if price < 1000:
            return False, "Минимальная цена - 1000 ₽"
        if price > 100_000_000:
            return False, "Максимальная цена - 100 000 000 ₽"
        
        return True, price
    except ValueError:
        return False, "Введите корректную цену (только цифры)"

def validate_mileage(mileage_text: str):
    """Проверка пробега"""
    # Убираем пробелы
    mileage_text = re.sub(r'[^\d]', '', mileage_text)
    
    try:
        mileage = int(mileage_text) if mileage_text else 0
        
        if mileage < 0:
            return False, "Пробег не может быть отрицательным"
        if mileage > 1_000_000:
            return False, "Пробег не может превышать 1 000 000 км"
        
        return True, mileage
    except ValueError:
        return False, "Введите корректный пробег (только цифры)"

def validate_engine_capacity(capacity_text: str):
    """Проверка объёма двигателя"""
    # Заменяем запятую на точку
    capacity_text = capacity_text.replace(',', '.')
    
    try:
        capacity = float(capacity_text)
        
        if capacity < 0.1 or capacity > 10.0:
            return False, "Объём двигателя должен быть от 0.1 до 10.0 литров"
        
        # Округляем до 1 знака
        return True, round(capacity, 1)
    except ValueError:
        return False, "Введите корректный объём (например: 2.0)"

def validate_phone(phone: str):
    """Простая проверка номера телефона"""
    # Убираем все нецифровые символы
    cleaned = re.sub(r'[^\d]', '', phone)
    
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False, "Номер телефона должен содержать 10-15 цифр"
    
    return True, cleaned

def validate_description(description: str, max_length: int = 1000):
    """Проверка описания"""
    if len(description) > max_length:
        return False, f"Описание слишком длинное (максимум {max_length} символов)"
    
    return True, description