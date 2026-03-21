from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import json
import logging

from database.db import get_db
from database.queries import UserQueries, AdQueries

logger = logging.getLogger(__name__)

async def my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать объявления пользователя"""
    user = update.effective_user
    
    try:
        async for session in get_db():
            db_user = await UserQueries.get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            ads = await AdQueries.get_user_ads(session, db_user.id)
        
        if not ads:
            text = "📭 У вас пока нет объявлений\n\nЧтобы создать объявление, нажмите /add"
            keyboard = [[InlineKeyboardButton("➕ Создать объявление", callback_data="add_ad_manual")]]
            keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        else:
            text = "📋 <b>Ваши объявления:</b>\n\n"
            keyboard = []
            
            for ad in ads:
                status = "✅ Активно" if ad.is_active else "⏸ Скрыто"
                price_str = f"{ad.price:,}".replace(',', ' ')
                
                text += (
                    f"🚗 <b>{ad.brand} {ad.model}</b>\n"
                    f"   📅 {ad.year} • {price_str} ₽\n"
                    f"   👁 {ad.views_count} просмотров • {status}\n"
                    f"   🆔 ID: {ad.id}\n\n"
                )
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"✏️ {ad.brand} {ad.model}",
                        callback_data=f"edit_{ad.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("➕ Новое объявление", callback_data="add_ad_manual")])
            keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error in my_ads: {e}")
        error_text = "❌ Произошла ошибка при загрузке ваших объявлений"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

async def edit_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирование объявления"""
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split('_')[1])
    
    try:
        async for session in get_db():
            ad = await AdQueries.get_ad_by_id(session, ad_id)
            
            if not ad:
                await query.edit_message_text("❌ Объявление не найдено")
                return
            
            price_str = f"{ad.price:,}".replace(',', ' ')
            
            text = (
                f"🚗 <b>{ad.brand} {ad.model}</b>\n\n"
                f"📅 Год: {ad.year}\n"
                f"💰 Цена: {price_str} ₽\n"
                f"📊 Пробег: {ad.mileage} км\n"
                f"⚙️ Двигатель: {ad.engine_capacity}л {ad.engine_type}\n"
                f"🔄 Коробка: {ad.transmission}\n"
                f"🎨 Цвет: {ad.color}\n\n"
                f"📊 <b>Статистика:</b>\n"
                f"👁 Просмотров: {ad.views_count}\n"
                f"📅 Размещено: {ad.created_at.strftime('%d.%m.%Y')}\n"
                f"📌 Статус: {'✅ Активно' if ad.is_active else '⏸ Скрыто'}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🚫 Удалить", callback_data=f"delete_{ad_id}")],
                [InlineKeyboardButton("🔄 Изменить статус", callback_data=f"toggle_{ad_id}")],
                [InlineKeyboardButton("📸 Добавить фото", callback_data=f"add_photo_{ad_id}")],
                [InlineKeyboardButton("💰 Изменить цену", callback_data=f"edit_price_{ad_id}")],
                [InlineKeyboardButton("◀️ Назад", callback_data="my_ads")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error editing ad: {e}")
        await query.edit_message_text("❌ Ошибка при загрузке объявления")

async def delete_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление объявления"""
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split('_')[1])
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{ad_id}"),
            InlineKeyboardButton("❌ Нет, отмена", callback_data=f"edit_{ad_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚠️ Вы уверены, что хотите удалить это объявление?\n"
        "Это действие нельзя отменить.",
        reply_markup=reply_markup
    )

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления"""
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split('_')[2])
    
    try:
        async for session in get_db():
            success = await AdQueries.delete_ad(session, ad_id)
            
            if success:
                await query.edit_message_text(
                    "✅ Объявление успешно удалено",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")
                    ]])
                )
            else:
                await query.edit_message_text("❌ Ошибка при удалении")
    except Exception as e:
        logger.error(f"Error deleting ad: {e}")
        await query.edit_message_text("❌ Ошибка при удалении объявления")

async def toggle_ad_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включение/выключение объявления"""
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split('_')[1])
    
    try:
        async for session in get_db():
            ad = await AdQueries.get_ad_by_id(session, ad_id)
            
            if ad:
                new_status = not ad.is_active
                await AdQueries.update_ad(session, ad_id, is_active=new_status)
                
                status_text = "активно" if new_status else "скрыто"
                await query.edit_message_text(
                    f"✅ Статус изменён: объявление теперь {status_text}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ Назад", callback_data=f"edit_{ad_id}")
                    ]])
                )
    except Exception as e:
        logger.error(f"Error toggling ad status: {e}")
        await query.edit_message_text("❌ Ошибка при изменении статуса")