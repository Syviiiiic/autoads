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
    raise ValueError("BOT_TOKEN is not set in environment")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        f"👋 Привет, {user.first_name}!\n\n🚘 Auto Ads Bot готов к работе!",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Помощь:\n/start — Главное меню\n/ads — Объявления\n/add — Добавить\n/myads — Мои"
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Web App data received")
    await update.message.reply_text("✅ Данные получены!")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    logger.error(f"Error: {context.error}")

async def main():
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)

    logger.info("Bot started successfully!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
