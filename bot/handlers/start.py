from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database.db import get_db
from database.queries import UserQueries
import os

MINI_APP_URL = os.getenv('MINI_APP_URL', 'http://localhost')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    async for session in get_db():
        await UserQueries.get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    
    keyboard = [
        [InlineKeyboardButton(
            "🚗 Открыть каталог авто",
            web_app=WebAppInfo(url=f"{MINI_APP_URL}")
        )],
        [InlineKeyboardButton("➕ Добавить объявление", callback_data="add_ad_manual")],
        [InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "🚘 <b>Auto Ads Bot</b> - площадка для продажи автомобилей\n\n"
        "Нажмите кнопку ниже чтобы открыть удобный каталог:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    text = (
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "📱 <b>Через Mini App:</b>\n"
        "• Нажмите 'Открыть каталог авто'\n"
        "• Удобный интерфейс с фильтрами\n\n"
        "💬 <b>Через команды:</b>\n"
        "/ads - все объявления\n"
        "/add - добавить вручную\n"
        "/myads - мои объявления\n\n"
        "❓ Вопросы: @username"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
            ]])
        )
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("🚗 Открыть каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
            [InlineKeyboardButton("➕ Добавить", callback_data="add_ad_manual")],
            [InlineKeyboardButton("📋 Мои", callback_data="my_ads")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        await query.edit_message_text(
            "🚘 Главное меню",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )