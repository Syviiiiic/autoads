import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from telegram.constants import ParseMode
from dotenv import load_dotenv
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_db
from database.queries import UserQueries, AdQueries

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_URL = os.getenv('API_URL', 'http://localhost:8000')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://your-domain.com')  # URL где будет размещён Mini App

# Состояния для ConversationHandler
(
    BRAND, MODEL, YEAR, PRICE, MILEAGE,
    ENGINE_TYPE, ENGINE_CAPACITY, TRANSMISSION, 
    DRIVE, COLOR, DESCRIPTION, PHOTOS
) = range(12)

# Временное хранилище для данных объявления
user_ad_data = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - показывает главное меню"""
    user = update.effective_user
    
    # Сохраняем пользователя в БД
    async for session in get_db():
        db_user = await UserQueries.get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    
    # Создаём клавиатуру с Web App кнопкой
    keyboard = [
        [InlineKeyboardButton(
            "🚗 Открыть каталог авто",
            web_app=WebAppInfo(url=f"{MINI_APP_URL}")
        )],
        [InlineKeyboardButton("➕ Добавить объявление (вручную)", callback_data="add_ad_manual")],
        [InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🚘 <b>Auto Ads Bot</b> - площадка для продажи автомобилей\n\n"
        "🔹 <b>Нажмите кнопку ниже</b> чтобы открыть удобный каталог\n"
        "🔹 Можно добавлять объявления через Mini App или вручную\n"
        "🔹 Все объявления синхронизируются автоматически\n\n"
        "<i>Выберите действие:</i>"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из Web App"""
    data = update.effective_message.web_app_data.data
    user = update.effective_user
    
    logger.info(f"Received Web App data from user {user.id}: {data}")
    
    # Здесь можно обработать данные, отправленные из Mini App
    # Например, уведомления о новых объявлениях и т.д.
    
    await update.message.reply_text(
        "✅ Данные получены! Спасибо за использование Mini App."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь по использованию"""
    help_text = (
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "📱 <b>Через Mini App (рекомендуется):</b>\n"
        "• Нажмите 'Открыть каталог авто'\n"
        "• Удобный интерфейс с фильтрами и поиском\n"
        "• Можно добавлять фото и смотреть детали\n\n"
        "💬 <b>Через команды бота:</b>\n"
        "/ads - посмотреть все объявления\n"
        "/add - добавить объявление вручную\n"
        "/myads - мои объявления\n"
        "/search - поиск\n\n"
        "❓ Если возникли вопросы, пишите @username"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
            ]])
        )
    else:
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "main_menu":
        await show_main_menu(query)
    elif data == "my_ads":
        await show_my_ads(query, context)
    elif data == "add_ad_manual":
        await start_manual_add(query, context)
    elif data == "help":
        await help_command(update, context)

async def show_main_menu(query):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton(
            "🚗 Открыть каталог авто",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )],
        [InlineKeyboardButton("➕ Добавить объявление (вручную)", callback_data="add_ad_manual")],
        [InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🚘 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def show_my_ads(query, context):
    """Показать объявления пользователя"""
    user_id = query.from_user.id
    
    async for session in get_db():
        user = await UserQueries.get_or_create_user(session, telegram_id=user_id)
        ads = await AdQueries.get_user_ads(session, user.id)
    
    if not ads:
        await query.edit_message_text(
            "📭 У вас пока нет объявлений",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Создать объявление", callback_data="add_ad_manual"),
                InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
            ]])
        )
        return
    
    text = "📋 <b>Ваши объявления:</b>\n\n"
    keyboard = []
    
    for ad in ads[:5]:  # Показываем последние 5
        status = "✅" if ad.is_active else "⏸"
        text += f"{status} <b>{ad.brand} {ad.model}</b> ({ad.year}) - {ad.price:,} ₽\n"
        keyboard.append([InlineKeyboardButton(
            f"✏️ {ad.brand} {ad.model}",
            callback_data=f"edit_ad_{ad.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("➕ Новое объявление", callback_data="add_ad_manual")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="main_menu")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

# ========== Ручное добавление объявления (на случай если Mini App не работает) ==========

async def start_manual_add(query, context):
    """Начало ручного добавления объявления"""
    user_id = query.from_user.id
    user_ad_data[user_id] = {}
    
    await query.edit_message_text(
        "🚗 <b>Добавление объявления вручную</b>\n\n"
        "Шаг 1: Введите марку автомобиля\n"
        "Например: Toyota, BMW, Lada\n\n"
        "<i>Или нажмите /cancel для отмены</i>",
        parse_mode=ParseMode.HTML
    )
    return BRAND

async def receive_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    brand = update.message.text.strip()
    
    user_ad_data[user_id]['brand'] = brand
    
    await update.message.reply_text(
        f"✅ Марка: {brand}\n\n"
        "Шаг 2: Введите модель"
    )
    return MODEL

async def receive_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    model = update.message.text.strip()
    
    user_ad_data[user_id]['model'] = model
    
    await update.message.reply_text(
        f"✅ Модель: {model}\n\n"
        "Шаг 3: Введите год выпуска"
    )
    return YEAR

async def receive_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        year = int(update.message.text.strip())
        if year < 1900 or year > 2026:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введите корректный год (1900-2026)")
        return YEAR
    
    user_ad_data[user_id]['year'] = year
    
    await update.message.reply_text(
        f"✅ Год: {year}\n\n"
        "Шаг 4: Введите цену в рублях"
    )
    return PRICE

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        price = int(update.message.text.replace(' ', ''))
    except ValueError:
        await update.message.reply_text("❌ Введите корректную цену (только цифры)")
        return PRICE
    
    user_ad_data[user_id]['price'] = price
    
    await update.message.reply_text(
        f"✅ Цена: {price:,} ₽\n\n"
        "Шаг 5: Введите пробег в км (или 0 для нового авто)",
        parse_mode=ParseMode.HTML
    )
    return MILEAGE

async def receive_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        mileage = int(update.message.text.replace(' ', ''))
    except ValueError:
        await update.message.reply_text("❌ Введите корректный пробег (только цифры)")
        return MILEAGE
    
    user_ad_data[user_id]['mileage'] = mileage
    
    keyboard = [["Бензин", "Дизель"], ["Электро", "Гибрид"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Пробег: {mileage:,} км\n\n"
        "Шаг 6: Выберите тип двигателя",
        reply_markup=reply_markup
    )
    return ENGINE_TYPE

async def receive_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    engine_type = update.message.text.strip()
    
    valid_engines = ["Бензин", "Дизель", "Электро", "Гибрид"]
    if engine_type not in valid_engines:
        await update.message.reply_text("❌ Выберите из предложенных вариантов")
        return ENGINE_TYPE
    
    user_ad_data[user_id]['engine_type'] = engine_type
    
    if engine_type == "Электро":
        user_ad_data[user_id]['engine_capacity'] = 0.0
        await update.message.reply_text(
            "Шаг 7: Выберите тип коробки передач",
            reply_markup=ReplyKeyboardMarkup([["Механика", "Автомат"], ["Робот", "Вариатор"]], 
                                           one_time_keyboard=True, resize_keyboard=True)
        )
        return TRANSMISSION
    else:
        await update.message.reply_text(
            "Введите объём двигателя в литрах",
            reply_markup=ReplyKeyboardRemove()
        )
        return ENGINE_CAPACITY

async def receive_engine_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        capacity = float(update.message.text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text("❌ Введите корректный объём (например: 2.0)")
        return ENGINE_CAPACITY
    
    user_ad_data[user_id]['engine_capacity'] = capacity
    
    await update.message.reply_text(
        "Шаг 7: Выберите тип коробки передач",
        reply_markup=ReplyKeyboardMarkup([["Механика", "Автомат"], ["Робот", "Вариатор"]], 
                                       one_time_keyboard=True, resize_keyboard=True)
    )
    return TRANSMISSION

async def receive_transmission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transmission = update.message.text.strip()
    
    valid_transmissions = ["Механика", "Автомат", "Робот", "Вариатор"]
    if transmission not in valid_transmissions:
        await update.message.reply_text("❌ Выберите из предложенных вариантов")
        return TRANSMISSION
    
    user_ad_data[user_id]['transmission'] = transmission
    
    await update.message.reply_text(
        "Шаг 8: Выберите тип привода",
        reply_markup=ReplyKeyboardMarkup([["Передний", "Задний"], ["Полный"]], 
                                       one_time_keyboard=True, resize_keyboard=True)
    )
    return DRIVE

async def receive_drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    drive = update.message.text.strip()
    
    valid_drives = ["Передний", "Задний", "Полный"]
    if drive not in valid_drives:
        await update.message.reply_text("❌ Выберите из предложенных вариантов")
        return DRIVE
    
    user_ad_data[user_id]['drive'] = drive
    
    await update.message.reply_text(
        "Шаг 9: Введите цвет автомобиля",
        reply_markup=ReplyKeyboardRemove()
    )
    return COLOR

async def receive_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    color = update.message.text.strip()
    
    user_ad_data[user_id]['color'] = color
    
    await update.message.reply_text(
        "Шаг 10: Опишите автомобиль (или отправьте пустое сообщение)"
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    description = update.message.text.strip()
    
    user_ad_data[user_id]['description'] = description
    
    await update.message.reply_text(
        "Шаг 11: Отправьте фотографии автомобиля (до 10 шт)\n"
        "После отправки всех фото нажмите /done"
    )
    return PHOTOS

async def receive_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if 'photos' not in user_ad_data[user_id]:
        user_ad_data[user_id]['photos'] = []
    
    photo = update.message.photo[-1]
    user_ad_data[user_id]['photos'].append(photo.file_id)
    
    count = len(user_ad_data[user_id]['photos'])
    await update.message.reply_text(f"✅ Фото {count}/10 добавлено")
    
    return PHOTOS

async def finish_manual_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if 'photos' not in user_ad_data[user_id]:
        await update.message.reply_text("❌ Нужно добавить хотя бы одно фото")
        return PHOTOS
    
    # Сохраняем в БД
    async for session in get_db():
        user = await UserQueries.get_or_create_user(session, telegram_id=user_id)
        
        ad_data = {
            'brand': user_ad_data[user_id]['brand'],
            'model': user_ad_data[user_id]['model'],
            'year': user_ad_data[user_id]['year'],
            'price': user_ad_data[user_id]['price'],
            'mileage': user_ad_data[user_id].get('mileage', 0),
            'engine_capacity': user_ad_data[user_id].get('engine_capacity', 0.0),
            'engine_type': user_ad_data[user_id].get('engine_type', 'Не указан'),
            'transmission': user_ad_data[user_id].get('transmission', 'Не указана'),
            'drive': user_ad_data[user_id].get('drive', 'Не указан'),
            'color': user_ad_data[user_id].get('color', 'Не указан'),
            'description': user_ad_data[user_id].get('description', ''),
            'photos': json.dumps(user_ad_data[user_id]['photos'])
        }
        
        await AdQueries.create_ad(session, user.id, ad_data)
    
    await update.message.reply_text(
        "✅ Объявление успешно создано!\n"
        "Посмотреть можно в каталоге или через /myads",
        reply_markup=ReplyKeyboardRemove()
    )
    
    del user_ad_data[user_id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_ad_data:
        del user_ad_data[user_id]
    
    await update.message.reply_text(
        "❌ Создание объявления отменено",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

async def main():
    """Главная функция"""
    # Инициализируем базу данных
    logger.info("Initializing database...")
    await init_db()
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Базовые команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Web App data handler
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Conversation handler для ручного добавления
    manual_add_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_manual_add, pattern="^add_ad_manual$")],
        states={
            BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_brand)],
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_model)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_year)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_price)],
            MILEAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mileage)],
            ENGINE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_engine)],
            ENGINE_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_engine_capacity)],
            TRANSMISSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_transmission)],
            DRIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_drive)],
            COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_color)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            PHOTOS: [
                MessageHandler(filters.PHOTO, receive_photos),
                CommandHandler("done", finish_manual_add)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(manual_add_handler)
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Бот запущен...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())