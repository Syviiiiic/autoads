import logging
import asyncio
import os
import sys
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Добавляем корень проекта в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_db
from database.queries import UserQueries

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'http://localhost')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set in environment")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    try:
        async for session in get_db():
            await UserQueries.get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        logger.info(f"User {user.id} saved")
    except Exception as e:
        logger.error(f"Error saving user: {e}")

    keyboard = [
        [InlineKeyboardButton("🚗 Открыть каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Мои", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n🚘 Auto Ads Bot готов к работе!\n\n"
        f"Нажмите кнопку 'Открыть каталог' для просмотра объявлений.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🔍 <b>Помощь</b>\n\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
        "Для просмотра объявлений используйте кнопку 'Открыть каталог'",
        parse_mode=ParseMode.HTML
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из Web App"""
    data = update.effective_message.web_app_data.data
    logger.info(f"Web App data received: {data[:100]}...")
    await update.message.reply_text("✅ Данные получены!")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "my_ads":
        await query.edit_message_text("📋 Мои объявления: пока пусто")
    elif query.data == "add":
        await query.edit_message_text("➕ Добавление объявления через Mini App")
    elif query.data == "help":
        await help_command(update, context)
    elif query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("🚗 Каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
            [InlineKeyboardButton("➕ Добавить", callback_data="add")],
            [InlineKeyboardButton("📋 Мои", callback_data="my_ads")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        await query.edit_message_text(
            "🚘 Главное меню",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Error: {context.error}")

# ========== ПРОСТАЯ И НАДЁЖНАЯ ТОЧКА ВХОДА ==========
def run_bot():
    """Запуск бота в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        loop.close()

async def main():
    """Главная функция бота"""
    logger.info("=" * 50)
    logger.info("Auto Ads Bot Starting...")
    logger.info("=" * 50)
    
    # Инициализация базы данных
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database ready")
    
    # Создание приложения
    logger.info("Building application...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    
    logger.info("Bot is ready! Starting polling...")
    logger.info(f"Bot URL: {MINI_APP_URL}")
    
    # Запуск поллинга
    await app.run_polling()

if __name__ == "__main__":
    run_bot()
