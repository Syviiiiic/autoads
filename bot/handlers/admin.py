from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

from database.db import get_db
from database.queries import UserQueries, AdQueries
from bot.config import Config

logger = logging.getLogger(__name__)
config = Config()

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Панель администратора"""
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь админом
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 Модерация", callback_data="admin_moderate")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 <b>Панель администратора</b>\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def moderate_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Модерация объявления"""
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split('_')[1])
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{ad_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{ad_id}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_moderate")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"Модерация объявления #{ad_id}\n\nПроверьте объявление и выберите действие:",
        reply_markup=reply_markup
    )