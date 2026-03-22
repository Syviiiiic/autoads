import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    DATABASE_URL = os.getenv('DATABASE_URL')
    API_URL = os.getenv('API_URL', 'http://185.56.162.203:8000')
    MINI_APP_URL = os.getenv('MINI_APP_URL', 'http://185.56.162.203')
    
    # Состояния для ConversationHandler
    BRAND, MODEL, YEAR, PRICE, MILEAGE = range(5)
    ENGINE_TYPE, ENGINE_CAPACITY, TRANSMISSION = range(5, 8)
    DRIVE, COLOR, DESCRIPTION, PHOTOS = range(8, 12)
