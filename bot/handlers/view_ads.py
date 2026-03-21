from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import json
import logging

from database.db import get_db
from database.queries import AdQueries
from bot.config import Config

logger = logging.getLogger(__name__)
config = Config()

# Хранилище для пагинации
user_page = {}

async def view_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр всех объявлений"""
    user_id = update.effective_user.id
    user_page[user_id] = 0
    
    await show_ads_page(update, context, user_id, 0)

async def show_ads_page(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, page: int):
    """Показать страницу с объявлениями"""
    try:
        async for session in get_db():
            ads = await AdQueries.get_ads(session, limit=config.ADS_PER_PAGE, offset=page * config.ADS_PER_PAGE)
            
            if not ads:
                text = "📭 Пока нет активных объявлений"
                if page > 0:
                    text = "📭 Больше объявлений нет"
                
                if isinstance(update, Update) and update.callback_query:
                    await update.callback_query.edit_message_text(text)
                else:
                    await update.message.reply_text(text)
                return
            
            text = "🚗 <b>Актуальные объявления:</b>\n\n"
            keyboard = []
            
            for i, ad in enumerate(ads, 1):
                price_str = f"{ad.price:,}".replace(',', ' ')
                mileage_str = f"{ad.mileage:,}".replace(',', ' ') if ad.mileage else "н/д"
                
                text += (
                    f"{i}. <b>{ad.brand} {ad.model}</b>\n"
                    f"   📅 {ad.year} • {price_str} ₽\n"
                    f"   📍 Пробег: {mileage_str} км\n"
                    f"   👁 Просмотров: {ad.views_count}\n\n"
                )
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔍 {ad.brand} {ad.model}",
                        callback_data=f"ad_{ad.id}"
                    )
                ])
            
            # Кнопки навигации
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"prev_{page}"))
            nav_buttons.append(InlineKeyboardButton(f"📄 {page+1}", callback_data="current"))
            nav_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"next_{page}"))
            
            keyboard.append(nav_buttons)
            keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if isinstance(update, Update) and update.callback_query:
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
        logger.error(f"Error showing ads page: {e}")
        error_text = "❌ Произошла ошибка при загрузке объявлений"
        if isinstance(update, Update) and update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

async def next_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Следующая страница"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    current_page = user_page.get(user_id, 0)
    next_page_num = current_page + 1
    
    user_page[user_id] = next_page_num
    await show_ads_page(update, context, user_id, next_page_num)

async def prev_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предыдущая страница"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    current_page = user_page.get(user_id, 0)
    
    if current_page > 0:
        prev_page_num = current_page - 1
        user_page[user_id] = prev_page_num
        await show_ads_page(update, context, user_id, prev_page_num)

async def show_ad_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать детали объявления"""
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split('_')[1])
    
    try:
        async for session in get_db():
            ad = await AdQueries.get_ad_by_id(session, ad_id)
            
            if not ad:
                await query.edit_message_text("❌ Объявление не найдено")
                return
            
            await AdQueries.increment_views(session, ad_id)
            
            price_str = f"{ad.price:,}".replace(',', ' ')
            mileage_str = f"{ad.mileage:,}".replace(',', ' ') if ad.mileage else "Не указан"
            engine_capacity = ad.engine_capacity if ad.engine_capacity else "—"
            
            photos = json.loads(ad.photos) if ad.photos else []
            
            text = (
                f"🚗 <b>{ad.brand} {ad.model}</b>\n\n"
                f"📅 Год: {ad.year}\n"
                f"💰 Цена: {price_str} ₽\n"
                f"📊 Пробег: {mileage_str} км\n"
                f"⚙️ Двигатель: {engine_capacity}л {ad.engine_type}\n"
                f"🔄 Коробка: {ad.transmission}\n"
                f"🔧 Привод: {ad.drive}\n"
                f"🎨 Цвет: {ad.color}\n\n"
                f"📝 <b>Описание:</b>\n{ad.description if ad.description else 'Нет описания'}\n\n"
                f"📞 <b>Продавец:</b> @{ad.owner.username if ad.owner.username else 'Не указан'}\n"
                f"👁 Просмотров: {ad.views_count + 1}\n"
                f"📅 Размещено: {ad.created_at.strftime('%d.%m.%Y')}"
            )
            
            keyboard = [
                [InlineKeyboardButton("📞 Связаться с продавцом", callback_data=f"contact_{ad.user_id}")],
                [InlineKeyboardButton("⭐ В избранное", callback_data=f"favorite_{ad_id}")],
                [InlineKeyboardButton("◀️ Назад к списку", callback_data="back_to_ads")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if photos:
                await query.message.delete()
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photos[0],
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
    except Exception as e:
        logger.error(f"Error showing ad details: {e}")
        await query.edit_message_text("❌ Ошибка при загрузке объявления")

async def search_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск объявлений"""
    text = (
        "🔍 <b>Поиск объявлений</b>\n\n"
        "Используйте Mini App для удобного поиска с фильтрами.\n\n"
        "Или команды:\n"
        "/search_brand [марка] - поиск по марке\n"
        "/search_price [мин] [макс] - поиск по цене\n"
        "/search_year [мин] [макс] - поиск по году\n\n"
        "Пример: /search_brand Toyota"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)