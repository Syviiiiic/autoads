from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
import json
import logging

from database.db import get_db
from database.queries import UserQueries, AdQueries
from bot.utils.validators import (
    validate_year, validate_price, validate_mileage,
    validate_engine_capacity
)
from bot.keyboards.reply_markups import get_cancel_keyboard

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    BRAND, MODEL, YEAR, PRICE, MILEAGE,
    ENGINE_TYPE, ENGINE_CAPACITY, TRANSMISSION,
    DRIVE, COLOR, DESCRIPTION, PHOTOS
) = range(12)

# Временное хранилище для данных объявления
user_ad_data = {}

async def add_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ручного добавления объявления"""
    user_id = update.effective_user.id
    user_ad_data[user_id] = {}
    
    text = (
        "🚗 <b>Добавление объявления вручную</b>\n\n"
        "Шаг 1/11: Введите марку автомобиля\n"
        "Например: Toyota, BMW, Lada\n\n"
        "<i>Или отправьте /cancel для отмены</i>"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML
        )
        return BRAND
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=get_cancel_keyboard()
        )
        return BRAND

async def receive_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение марки"""
    user_id = update.effective_user.id
    brand = update.message.text.strip()
    
    if len(brand) > 100:
        await update.message.reply_text(
            "❌ Слишком длинное название. Введите короче:",
            reply_markup=get_cancel_keyboard()
        )
        return BRAND
    
    user_ad_data[user_id]['brand'] = brand
    
    await update.message.reply_text(
        f"✅ Марка: {brand}\n\n"
        "Шаг 2/11: Введите модель автомобиля",
        reply_markup=get_cancel_keyboard()
    )
    return MODEL

async def receive_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение модели"""
    user_id = update.effective_user.id
    model = update.message.text.strip()
    
    if len(model) > 100:
        await update.message.reply_text(
            "❌ Слишком длинное название. Введите короче:",
            reply_markup=get_cancel_keyboard()
        )
        return MODEL
    
    user_ad_data[user_id]['model'] = model
    
    await update.message.reply_text(
        f"✅ Модель: {model}\n\n"
        "Шаг 3/11: Введите год выпуска\n"
        "Например: 2020",
        reply_markup=get_cancel_keyboard()
    )
    return YEAR

async def receive_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение года"""
    user_id = update.effective_user.id
    year_text = update.message.text.strip()
    
    is_valid, year_or_error = validate_year(year_text)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {year_or_error}",
            reply_markup=get_cancel_keyboard()
        )
        return YEAR
    
    user_ad_data[user_id]['year'] = year_or_error
    
    await update.message.reply_text(
        f"✅ Год: {year_or_error}\n\n"
        "Шаг 4/11: Введите цену в рублях\n"
        "Например: 1500000",
        reply_markup=get_cancel_keyboard()
    )
    return PRICE

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение цены"""
    user_id = update.effective_user.id
    price_text = update.message.text.strip()
    
    is_valid, price_or_error = validate_price(price_text)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {price_or_error}",
            reply_markup=get_cancel_keyboard()
        )
        return PRICE
    
    user_ad_data[user_id]['price'] = price_or_error
    
    await update.message.reply_text(
        f"✅ Цена: {price_or_error:,} ₽\n\n"
        "Шаг 5/11: Введите пробег в км (или 0 для нового авто)",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return MILEAGE

async def receive_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение пробега"""
    user_id = update.effective_user.id
    mileage_text = update.message.text.strip()
    
    is_valid, mileage_or_error = validate_mileage(mileage_text)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {mileage_or_error}",
            reply_markup=get_cancel_keyboard()
        )
        return MILEAGE
    
    user_ad_data[user_id]['mileage'] = mileage_or_error
    
    # Клавиатура для типа двигателя
    keyboard = [["Бензин", "Дизель"], ["Электро", "Гибрид"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Пробег: {mileage_or_error:,} км\n\n"
        "Шаг 6/11: Выберите тип двигателя",
        reply_markup=reply_markup
    )
    return ENGINE_TYPE

async def receive_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение типа двигателя"""
    user_id = update.effective_user.id
    engine_type = update.message.text.strip()
    
    valid_engines = ["Бензин", "Дизель", "Электро", "Гибрид"]
    if engine_type not in valid_engines:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите из предложенных вариантов",
            reply_markup=ReplyKeyboardMarkup([["Бензин", "Дизель"], ["Электро", "Гибрид"]], 
                                            one_time_keyboard=True, resize_keyboard=True)
        )
        return ENGINE_TYPE
    
    user_ad_data[user_id]['engine_type'] = engine_type
    
    if engine_type == "Электро":
        user_ad_data[user_id]['engine_capacity'] = 0.0
        
        # Клавиатура для КПП
        keyboard = [["Механика", "Автомат"], ["Робот", "Вариатор"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"✅ Тип двигателя: {engine_type}\n\n"
            "Шаг 7/11: Выберите тип коробки передач",
            reply_markup=reply_markup
        )
        return TRANSMISSION
    else:
        await update.message.reply_text(
            f"✅ Тип двигателя: {engine_type}\n\n"
            "Введите объём двигателя в литрах\n"
            "Например: 2.0",
            reply_markup=ReplyKeyboardRemove()
        )
        return ENGINE_CAPACITY

async def receive_engine_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение объёма двигателя"""
    user_id = update.effective_user.id
    capacity_text = update.message.text.strip()
    
    is_valid, capacity_or_error = validate_engine_capacity(capacity_text)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {capacity_or_error}",
            reply_markup=get_cancel_keyboard()
        )
        return ENGINE_CAPACITY
    
    user_ad_data[user_id]['engine_capacity'] = capacity_or_error
    
    # Клавиатура для КПП
    keyboard = [["Механика", "Автомат"], ["Робот", "Вариатор"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Объём: {capacity_or_error} л\n\n"
        "Шаг 7/11: Выберите тип коробки передач",
        reply_markup=reply_markup
    )
    return TRANSMISSION

async def receive_transmission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение типа КПП"""
    user_id = update.effective_user.id
    transmission = update.message.text.strip()
    
    valid_transmissions = ["Механика", "Автомат", "Робот", "Вариатор"]
    if transmission not in valid_transmissions:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите из предложенных вариантов",
            reply_markup=ReplyKeyboardMarkup([["Механика", "Автомат"], ["Робот", "Вариатор"]], 
                                            one_time_keyboard=True, resize_keyboard=True)
        )
        return TRANSMISSION
    
    user_ad_data[user_id]['transmission'] = transmission
    
    # Клавиатура для привода
    keyboard = [["Передний", "Задний"], ["Полный"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Коробка: {transmission}\n\n"
        "Шаг 8/11: Выберите тип привода",
        reply_markup=reply_markup
    )
    return DRIVE

async def receive_drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение типа привода"""
    user_id = update.effective_user.id
    drive = update.message.text.strip()
    
    valid_drives = ["Передний", "Задний", "Полный"]
    if drive not in valid_drives:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите из предложенных вариантов",
            reply_markup=ReplyKeyboardMarkup([["Передний", "Задний"], ["Полный"]], 
                                            one_time_keyboard=True, resize_keyboard=True)
        )
        return DRIVE
    
    user_ad_data[user_id]['drive'] = drive
    
    await update.message.reply_text(
        f"✅ Привод: {drive}\n\n"
        "Шаг 9/11: Введите цвет автомобиля\n"
        "Например: Белый, Чёрный, Синий",
        reply_markup=ReplyKeyboardRemove()
    )
    return COLOR

async def receive_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение цвета"""
    user_id = update.effective_user.id
    color = update.message.text.strip()
    
    if len(color) > 50:
        await update.message.reply_text(
            "❌ Слишком длинное название. Введите короче:",
            reply_markup=get_cancel_keyboard()
        )
        return COLOR
    
    user_ad_data[user_id]['color'] = color
    
    await update.message.reply_text(
        f"✅ Цвет: {color}\n\n"
        "Шаг 10/11: Опишите автомобиль\n"
        "Можно отправить пустое сообщение",
        reply_markup=get_cancel_keyboard()
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение описания"""
    user_id = update.effective_user.id
    description = update.message.text.strip()
    
    user_ad_data[user_id]['description'] = description
    
    await update.message.reply_text(
        "✅ Описание сохранено\n\n"
        "Шаг 11/11: Загрузите фотографии автомобиля\n"
        "Можно отправить до 10 фото\n"
        "После отправки всех фото нажмите /done",
        reply_markup=ReplyKeyboardRemove()
    )
    return PHOTOS

async def receive_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение фотографий"""
    user_id = update.effective_user.id
    
    if 'photos' not in user_ad_data[user_id]:
        user_ad_data[user_id]['photos'] = []
    
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    user_ad_data[user_id]['photos'].append(file_id)
    photos_count = len(user_ad_data[user_id]['photos'])
    
    if photos_count >= 10:
        await finish_manual_add(update, context)
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ Фото {photos_count}/10 добавлено\n"
        "Отправьте ещё фото или нажмите /done для завершения"
    )
    return PHOTOS

async def finish_manual_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение создания объявления"""
    user_id = update.effective_user.id
    user = update.effective_user
    
    if 'photos' not in user_ad_data[user_id] or not user_ad_data[user_id]['photos']:
        await update.message.reply_text(
            "❌ Нужно добавить хотя бы одно фото\n"
            "Отправьте фото или нажмите /cancel для отмены"
        )
        return PHOTOS
    
    try:
        async for session in get_db():
            db_user = await UserQueries.get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
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
            
            ad = await AdQueries.create_ad(session, db_user.id, ad_data)
            logger.info(f"Ad created: {ad.id} by user {user.id}")
        
        await update.message.reply_text(
            "✅ <b>Объявление успешно создано!</b>\n\n"
            f"🚗 {user_ad_data[user_id]['brand']} {user_ad_data[user_id]['model']}\n"
            f"📅 {user_ad_data[user_id]['year']} года\n"
            f"💰 {user_ad_data[user_id]['price']:,} ₽\n\n"
            "Объявление опубликовано и доступно в каталоге.",
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove()
        )
        
    except Exception as e:
        logger.error(f"Error creating ad: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при создании объявления. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    finally:
        if user_id in user_ad_data:
            del user_ad_data[user_id]
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания объявления"""
    user_id = update.effective_user.id
    if user_id in user_ad_data:
        del user_ad_data[user_id]
    
    await update.message.reply_text(
        "❌ Создание объявления отменено",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ConversationHandler для ручного добавления
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("add", add_ad_start),
        CallbackQueryHandler(add_ad_start, pattern="^add_ad_manual$")
    ],
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