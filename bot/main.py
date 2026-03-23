import asyncio
import logging
import sys
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,  # ← ИСПРАВЛЕНО
    MessageHandler,
    filters,
)

import config
from database.db import init_db, get_db
from services.car_service import CarService
from services.user_service import UserService
from services.admin_service import AdminService
from utils.helpers import format_car_info, create_car_keyboard

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    MAIN_MENU,
    CATALOG,
    CAR_DETAILS,
    ADD_CAR_BRAND,
    ADD_CAR_MODEL,
    ADD_CAR_YEAR,
    ADD_CAR_PRICE,
    ADD_CAR_DESCRIPTION,
    ADD_CAR_PHOTOS,
    ADD_CAR_CONTACT,
    SEARCH_BRAND,
    SEARCH_PRICE_MIN,
    SEARCH_PRICE_MAX,
    ADMIN_PANEL,
    ADMIN_CAR_APPROVE,
    ADMIN_CAR_REJECT,
    ADMIN_BROADCAST,
) = range(16)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message and main menu."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Register or update user
    with get_db() as db:
        user_service = UserService(db)
        user_service.create_or_update_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    
    keyboard = [
        [InlineKeyboardButton("🚗 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("➕ Подать объявление", callback_data="add_car")],
        [InlineKeyboardButton("🔍 Поиск", callback_data="search")],
        [InlineKeyboardButton("👤 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❤️ Избранное", callback_data="favorites")],
    ]
    
    # Add admin button if user is admin
    if user.id in config.ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔐 Админ панель", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Добро пожаловать в AutoAds - бот для продажи автомобилей.\n\n"
        "Выберите действие:",
        reply_markup=reply_markup,
    )
    
    return MAIN_MENU


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show main menu."""
    return await start(update, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "catalog":
        return await show_catalog(update, context)
    elif data == "add_car":
        return await start_add_car(update, context)
    elif data == "search":
        return await start_search(update, context)
    elif data == "my_ads":
        return await show_my_ads(update, context)
    elif data == "favorites":
        return await show_favorites(update, context)
    elif data == "admin":
        return await admin_panel(update, context)
    elif data.startswith("car_"):
        car_id = int(data.split("_")[1])
        return await show_car_details(update, context, car_id)
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        return await show_catalog(update, context, page)
    elif data.startswith("favorite_"):
        car_id = int(data.split("_")[1])
        return await toggle_favorite(update, context, car_id)
    elif data == "back_to_menu":
        return await start(update, context)
    elif data == "back_to_catalog":
        return await show_catalog(update, context)
    
    return MAIN_MENU


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0) -> int:
    """Show car catalog with pagination."""
    query = update.callback_query
    
    with get_db() as db:
        car_service = CarService(db)
        cars, total = car_service.get_approved_cars(page=page, per_page=5)
    
    if not cars:
        text = "📭 В каталоге пока нет объявлений."
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    else:
        text = f"🚗 Каталог автомобилей (страница {page + 1}):\n\n"
        keyboard = []
        
        for car in cars:
            text += format_car_info(car, short=True) + "\n"
            keyboard.append([InlineKeyboardButton(
                f"{car.brand} {car.model} - {car.price} ₽", 
                callback_data=f"car_{car.id}"
            )])
        
        # Pagination buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}"))
        if total > (page + 1) * 5:
            nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return CATALOG


async def show_car_details(update: Update, context: ContextTypes.DEFAULT_TYPE, car_id: int) -> int:
    """Show detailed car information."""
    query = update.callback_query
    
    with get_db() as db:
        car_service = CarService(db)
        car = car_service.get_car_by_id(car_id)
        
        if not car:
            await query.edit_message_text("❌ Объявление не найдено.")
            return CATALOG
        
        user_service = UserService(db)
        is_favorite = user_service.is_favorite(update.effective_user.id, car_id)
    
    text = format_car_info(car, short=False)
    
    keyboard = create_car_keyboard(car_id, is_favorite)
    keyboard.append([InlineKeyboardButton("🔙 Назад к каталогу", callback_data="back_to_catalog")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send photos if available
    if car.photos:
        media = [InputMediaPhoto(photo) for photo in car.photos[:5]]
        await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
    
    return CAR_DETAILS


async def start_add_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start car addition process."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 Давайте создадим объявление о продаже автомобиля.\n\n"
        "Шаг 1/6: Введите марку автомобиля (например: Toyota):"
    )
    
    return ADD_CAR_BRAND


async def add_car_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save car brand and ask for model."""
    context.user_data["brand"] = update.message.text
    
    await update.message.reply_text(
        "Шаг 2/6: Введите модель автомобиля (например: Camry):"
    )
    
    return ADD_CAR_MODEL


async def add_car_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save car model and ask for year."""
    context.user_data["model"] = update.message.text
    
    await update.message.reply_text(
        "Шаг 3/6: Введите год выпуска (например: 2020):"
    )
    
    return ADD_CAR_YEAR


async def add_car_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save car year and ask for price."""
    try:
        year = int(update.message.text)
        if year < 1900 or year > datetime.now().year + 1:
            raise ValueError
        context.user_data["year"] = year
    except ValueError:
        await update.message.reply_text(
            "❌ Некорректный год. Пожалуйста, введите год в формате YYYY:"
        )
        return ADD_CAR_YEAR
    
    await update.message.reply_text(
        "Шаг 4/6: Введите цену в рублях (например: 1500000):"
    )
    
    return ADD_CAR_PRICE


async def add_car_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save car price and ask for description."""
    try:
        price = int(update.message.text.replace(" ", "").replace("₽", ""))
        if price <= 0:
            raise ValueError
        context.user_data["price"] = price
    except ValueError:
        await update.message.reply_text(
            "❌ Некорректная цена. Пожалуйста, введите число:"
        )
        return ADD_CAR_PRICE
    
    await update.message.reply_text(
        "Шаг 5/6: Введите описание автомобиля (состояние, комплектация и т.д.):"
    )
    
    return ADD_CAR_DESCRIPTION


async def add_car_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save car description and ask for photos."""
    context.user_data["description"] = update.message.text
    
    await update.message.reply_text(
        "Шаг 6/6: Отправьте фотографии автомобиля (до 5 штук).\n"
        "Или отправьте /skip чтобы пропустить:"
    )
    
    context.user_data["photos"] = []
    return ADD_CAR_PHOTOS


async def add_car_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save car photos and ask for contact."""
    if update.message.photo:
        photo_file = update.message.photo[-1].file_id
        context.user_data["photos"].append(photo_file)
        
        if len(context.user_data["photos"]) >= 5:
            await update.message.reply_text(
                "✅ Максимальное количество фото получено.\n"
                "Теперь введите ваш контактный телефон:"
            )
            return ADD_CAR_CONTACT
        else:
            await update.message.reply_text(
                f"📸 Получено {len(context.user_data['photos'])} фото. "
                "Отправьте еще или введите телефон:"
            )
            return ADD_CAR_PHOTOS
    
    elif update.message.text and not update.message.text.startswith("/"):
        # User sent contact info instead of photo
        context.user_data["contact"] = update.message.text
        return await finish_add_car(update, context)
    
    await update.message.reply_text("Пожалуйста, отправьте фото или контактную информацию:")
    return ADD_CAR_PHOTOS


async def skip_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip photo upload."""
    await update.message.reply_text(
        "Фото пропущены. Введите ваш контактный телефон:"
    )
    return ADD_CAR_CONTACT


async def add_car_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save contact and finish car addition."""
    context.user_data["contact"] = update.message.text
    return await finish_add_car(update, context)


async def finish_add_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finish car addition and save to database."""
    user = update.effective_user
    
    with get_db() as db:
        car_service = CarService(db)
        car = car_service.create_car(
            user_id=user.id,
            brand=context.user_data["brand"],
            model=context.user_data["model"],
            year=context.user_data["year"],
            price=context.user_data["price"],
            description=context.user_data["description"],
            photos=context.user_data.get("photos", []),
            contact=context.user_data["contact"],
        )
    
    # Notify admins
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🆕 Новое объявление на модерацию:\n\n"
                     f"{context.user_data['brand']} {context.user_data['model']}\n"
                     f"Год: {context.user_data['year']}\n"
                     f"Цена: {context.user_data['price']} ₽\n\n"
                     f"ID: {car.id}",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_approve_{car.id}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{car.id}"),
                    ]
                ]),
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    await update.message.reply_text(
        "✅ Ваше объявление отправлено на модерацию!\n"
        "После проверки администратором оно появится в каталоге.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]
        ]),
    )
    
    # Clear user data
    context.user_data.clear()
    return MAIN_MENU


async def show_my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user's ads."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    with get_db() as db:
        car_service = CarService(db)
        cars = car_service.get_user_cars(user_id)
    
    if not cars:
        text = "📭 У вас пока нет объявлений."
    else:
        text = "📝 Ваши объявления:\n\n"
        for car in cars:
            status = "✅" if car.is_approved else "⏳"
            text += f"{status} {car.brand} {car.model} - {car.price} ₽\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return MAIN_MENU


async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user's favorite cars."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    with get_db() as db:
        user_service = UserService(db)
        cars = user_service.get_favorites(user_id)
    
    if not cars:
        text = "📭 У вас пока нет избранных объявлений."
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    else:
        text = "❤️ Ваше избранное:\n\n"
        keyboard = []
        for car in cars:
            text += f"🚗 {car.brand} {car.model} - {car.price} ₽\n"
            keyboard.append([InlineKeyboardButton(
                f"{car.brand} {car.model}", callback_data=f"car_{car.id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return MAIN_MENU


async def toggle_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE, car_id: int) -> int:
    """Toggle favorite status for a car."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    with get_db() as db:
        user_service = UserService(db)
        is_fav = user_service.toggle_favorite(user_id, car_id)
    
    action = "добавлено в избранное" if is_fav else "удалено из избранного"
    await query.answer(f"❤️ {action}!")
    
    return await show_car_details(update, context, car_id)


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start search process."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 Поиск автомобилей\n\n"
        "Введите марку для поиска (или /skip для любой):"
    )
    
    return SEARCH_BRAND


async def search_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save search brand and ask for price range."""
    if update.message.text != "/skip":
        context.user_data["search_brand"] = update.message.text
    
    await update.message.reply_text(
        "Введите минимальную цену (или /skip):"
    )
    return SEARCH_PRICE_MIN


async def search_price_min(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save min price and ask for max price."""
    if update.message.text != "/skip":
        try:
            context.user_data["search_price_min"] = int(update.message.text)
        except ValueError:
            await update.message.reply_text("❌ Введите число или /skip:")
            return SEARCH_PRICE_MIN
    
    await update.message.reply_text("Введите максимальную цену (или /skip):")
    return SEARCH_PRICE_MAX


async def search_price_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Perform search with filters."""
    if update.message.text != "/skip":
        try:
            context.user_data["search_price_max"] = int(update.message.text)
        except ValueError:
            await update.message.reply_text("❌ Введите число или /skip:")
            return SEARCH_PRICE_MAX
    
    # Perform search
    with get_db() as db:
        car_service = CarService(db)
        cars = car_service.search_cars(
            brand=context.user_data.get("search_brand"),
            price_min=context.user_data.get("search_price_min"),
            price_max=context.user_data.get("search_price_max"),
        )
    
    if not cars:
        text = "🔍 По вашему запросу ничего не найдено."
    else:
        text = f"🔍 Найдено {len(cars)} автомобилей:\n\n"
        for car in cars:
            text += format_car_info(car, short=True) + "\n"
    
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    context.user_data.clear()
    return MAIN_MENU


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin panel."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_IDS:
        await query.answer("❌ Доступ запрещен!")
        return MAIN_MENU
    
    keyboard = [
        [InlineKeyboardButton("📋 Модерация", callback_data="admin_moderation")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")],
    ]
    
    await query.edit_message_text(
        "🔐 Панель администратора\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    
    return ADMIN_PANEL


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin statistics."""
    query = update.callback_query
    
    with get_db() as db:
        admin_service = AdminService(db)
        stats = admin_service.get_statistics()
    
    text = (
        "📊 Статистика:\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🚗 Объявлений всего: {stats['total_cars']}\n"
        f"✅ Одобрено: {stats['approved_cars']}\n"
        f"⏳ На модерации: {stats['pending_cars']}\n"
        f"❤️ Избранных: {stats['total_favorites']}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin")]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_PANEL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation."""
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]
        ]),
    )
    return MAIN_MENU


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )


def main() -> None:
    """Start the bot."""
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add conversation handler
    conv_handler = ConversationHandler(  # ← ИСПРАВЛЕНО: было ConversationTypes
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_handler),
            ],
            CATALOG: [
                CallbackQueryHandler(button_handler),
            ],
            CAR_DETAILS: [
                CallbackQueryHandler(button_handler),
            ],
            ADD_CAR_BRAND: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_brand),
            ],
            ADD_CAR_MODEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_model),
            ],
            ADD_CAR_YEAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_year),
            ],
            ADD_CAR_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_price),
            ],
            ADD_CAR_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_description),
            ],
            ADD_CAR_PHOTOS: [
                MessageHandler(filters.PHOTO, add_car_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_photos),
                CommandHandler("skip", skip_photos),
            ],
            ADD_CAR_CONTACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_car_contact),
            ],
            SEARCH_BRAND: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_brand),
                CommandHandler("skip", search_brand),
            ],
            SEARCH_PRICE_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_price_min),
                CommandHandler("skip", search_price_min),
            ],
            SEARCH_PRICE_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_price_max),
                CommandHandler("skip", search_price_max),
            ],
            ADMIN_PANEL: [
                CallbackQueryHandler(button_handler),
                CallbackQueryHandler(admin_stats, pattern="^admin_stats$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_error_handler(error_handler)
    
    logger.info("Bot started!")
    
    # Запуск без asyncio.run()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
