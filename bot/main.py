import logging
import asyncio
import os
import sys
import threading
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'http://localhost')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set")
    sys.exit(1)

# Отложенный импорт для асинхронной инициализации (выполнится в фоновом потоке)
def init_db_background():
    import asyncio
    from database.db import init_db
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    loop.close()

# Запускаем инициализацию БД в фоновом потоке
threading.Thread(target=init_db_background, daemon=True).start()

# Импортируем классы для работы с БД только внутри функций, чтобы избежать конфликтов
# from database.queries import UserQueries, AdQueries  # не импортируем глобально

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        from database.db import get_db
        from database.queries import UserQueries
        async for session in get_db():
            await UserQueries.get_or_create_user(session, telegram_id=user.id, username=user.username,
                                                  first_name=user.first_name, last_name=user.last_name)
    except Exception as e:
        logger.error(f"Error saving user: {e}")
    keyboard = [
        [InlineKeyboardButton("🚗 Открыть каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("➕ Добавить", callback_data="add_ad")],
        [InlineKeyboardButton("📋 Мои", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n🚘 Auto Ads Bot готов к работе!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔍 Помощь:\n/start - Главное меню\n/help - Эта справка\n\nДля просмотра объявлений используйте кнопку 'Открыть каталог'."
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]]))
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def myads_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        from database.db import get_db
        from database.queries import UserQueries, AdQueries
        async for session in get_db():
            db_user = await UserQueries.get_or_create_user(session, telegram_id=user.id)
            ads = await AdQueries.get_user_ads(session, db_user.id)
        if not ads:
            await update.message.reply_text("📭 У вас пока нет объявлений.")
            return
        text = "📋 <b>Ваши объявления:</b>\n\n"
        for ad in ads[:5]:
            status = "✅" if ad.is_active else "⏸"
            text += f"{status} <b>{ad.brand} {ad.model}</b> ({ad.year}) - {ad.price:,} ₽\n"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in myads_command: {e}")
        await update.message.reply_text("❌ Ошибка загрузки")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "main_menu":
        await show_main_menu(query)
    elif data == "my_ads":
        await show_my_ads(query)
    elif data == "add_ad":
        await query.edit_message_text("➕ Используйте Mini App для добавления")
    elif data == "help":
        await help_command(update, context)

async def show_main_menu(query):
    keyboard = [
        [InlineKeyboardButton("🚗 Каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("➕ Добавить", callback_data="add_ad")],
        [InlineKeyboardButton("📋 Мои", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    await query.edit_message_text("🚘 Главное меню", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_my_ads(query):
    user_id = query.from_user.id
    try:
        from database.db import get_db
        from database.queries import UserQueries, AdQueries
        async for session in get_db():
            user = await UserQueries.get_or_create_user(session, telegram_id=user_id)
            ads = await AdQueries.get_user_ads(session, user.id)
        if not ads:
            await query.edit_message_text("📭 У вас пока нет объявлений.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]]))
            return
        text = "📋 <b>Ваши объявления:</b>\n\n"
        keyboard = []
        for ad in ads[:5]:
            status = "✅" if ad.is_active else "⏸"
            text += f"{status} <b>{ad.brand} {ad.model}</b> ({ad.year}) - {ad.price:,} ₽\n"
            keyboard.append([InlineKeyboardButton(f"✏️ {ad.brand} {ad.model}", callback_data=f"edit_{ad.id}")])
        keyboard.append([InlineKeyboardButton("➕ Новое", callback_data="add_ad")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="main_menu")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error showing my ads: {e}")
        await query.edit_message_text("❌ Ошибка загрузки")

async def error_handler(update, context):
    logger.error(f"Exception: {context.error}", exc_info=True)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myads", myads_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, lambda u, c: u.message.reply_text("✅")))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
