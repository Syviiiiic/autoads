from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from .models import User, Ad, Favorite
import json
import logging

logger = logging.getLogger(__name__)

class UserQueries:
    @staticmethod
    async def get_or_create_user(session: AsyncSession, telegram_id: int, **kwargs) -> User:
        """Получить пользователя или создать нового"""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=kwargs.get('username'),
                first_name=kwargs.get('first_name'),
                last_name=kwargs.get('last_name')
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created new user: {telegram_id}")
        
        return user
    
    @staticmethod
    async def update_phone(session: AsyncSession, telegram_id: int, phone: str) -> bool:
        """Обновить телефон пользователя"""
        result = await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(phone=phone)
            .returning(User.id)
        )
        await session.commit()
        return result.first() is not None
    
    @staticmethod
    async def update_activity(session: AsyncSession, telegram_id: int):
        """Обновить время последней активности"""
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_activity=func.now())
        )
        await session.commit()

class AdQueries:
    @staticmethod
    async def create_ad(session: AsyncSession, user_id: int, ad_data: Dict[str, Any]) -> Ad:
        """Создать новое объявление"""
        if 'photos' in ad_data and isinstance(ad_data['photos'], list):
            ad_data['photos'] = json.dumps(ad_data['photos'])
        
        ad = Ad(user_id=user_id, **ad_data)
        session.add(ad)
        await session.commit()
        await session.refresh(ad)
        logger.info(f"Created ad {ad.id} for user {user_id}")
        return ad
    
    @staticmethod
    async def get_ads(session: AsyncSession, 
                      filters: Optional[Dict] = None,
                      limit: int = 10,
                      offset: int = 0) -> List[Ad]:
        """Получить объявления с фильтрацией"""
        query = select(Ad).where(Ad.is_active == True)
        
        if filters:
            if filters.get('brand'):
                query = query.where(Ad.brand.ilike(f"%{filters['brand']}%"))
            if filters.get('model'):
                query = query.where(Ad.model.ilike(f"%{filters['model']}%"))
            if filters.get('price_min'):
                query = query.where(Ad.price >= filters['price_min'])
            if filters.get('price_max'):
                query = query.where(Ad.price <= filters['price_max'])
            if filters.get('year_min'):
                query = query.where(Ad.year >= filters['year_min'])
            if filters.get('year_max'):
                query = query.where(Ad.year <= filters['year_max'])
        
        query = query.order_by(Ad.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def count_ads(session: AsyncSession, filters: Optional[Dict] = None) -> int:
        """Подсчитать количество объявлений с фильтрацией"""
        query = select(func.count(Ad.id)).where(Ad.is_active == True)
        
        if filters:
            if filters.get('brand'):
                query = query.where(Ad.brand.ilike(f"%{filters['brand']}%"))
            if filters.get('model'):
                query = query.where(Ad.model.ilike(f"%{filters['model']}%"))
            if filters.get('price_min'):
                query = query.where(Ad.price >= filters['price_min'])
            if filters.get('price_max'):
                query = query.where(Ad.price <= filters['price_max'])
        
        result = await session.execute(query)
        return result.scalar()
    
    @staticmethod
    async def get_user_ads(session: AsyncSession, user_id: int) -> List[Ad]:
        """Получить объявления пользователя"""
        result = await session.execute(
            select(Ad).where(Ad.user_id == user_id).order_by(Ad.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_ad_by_id(session: AsyncSession, ad_id: int) -> Optional[Ad]:
        """Получить объявление по ID"""
        result = await session.execute(
            select(Ad).where(Ad.id == ad_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_ad(session: AsyncSession, ad_id: int, **kwargs) -> bool:
        """Обновить объявление"""
        result = await session.execute(
            update(Ad)
            .where(Ad.id == ad_id)
            .values(**kwargs, updated_at=func.now())
            .returning(Ad.id)
        )
        await session.commit()
        return result.first() is not None
    
    @staticmethod
    async def delete_ad(session: AsyncSession, ad_id: int) -> bool:
        """Удалить объявление"""
        result = await session.execute(
            delete(Ad).where(Ad.id == ad_id).returning(Ad.id)
        )
        await session.commit()
        return result.first() is not None
    
    @staticmethod
    async def increment_views(session: AsyncSession, ad_id: int):
        """Увеличить счётчик просмотров"""
        await session.execute(
            update(Ad)
            .where(Ad.id == ad_id)
            .values(views_count=Ad.views_count + 1)
        )
        await session.commit()
    
    @staticmethod
    async def get_user_stats(session: AsyncSession, user_id: int) -> Dict[str, int]:
        """Получить статистику пользователя по объявлениям"""
        total_result = await session.execute(
            select(func.count(Ad.id)).where(Ad.user_id == user_id)
        )
        active_result = await session.execute(
            select(func.count(Ad.id)).where(Ad.user_id == user_id, Ad.is_active == True)
        )
        views_result = await session.execute(
            select(func.sum(Ad.views_count)).where(Ad.user_id == user_id)
        )
        
        return {
            "total_ads": total_result.scalar() or 0,
            "active_ads": active_result.scalar() or 0,
            "total_views": views_result.scalar() or 0
        }

class FavoriteQueries:
    @staticmethod
    async def add_favorite(session: AsyncSession, user_id: int, ad_id: int) -> bool:
        """Добавить в избранное"""
        try:
            favorite = Favorite(user_id=user_id, ad_id=ad_id)
            session.add(favorite)
            await session.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    async def remove_favorite(session: AsyncSession, user_id: int, ad_id: int) -> bool:
        """Удалить из избранного"""
        result = await session.execute(
            delete(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.ad_id == ad_id
            )
        )
        await session.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def get_user_favorites(session: AsyncSession, user_id: int) -> List[Ad]:
        """Получить избранные объявления пользователя"""
        result = await session.execute(
            select(Ad)
            .join(Favorite)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def is_favorite(session: AsyncSession, user_id: int, ad_id: int) -> bool:
        """Проверить, находится ли объявление в избранном"""
        result = await session.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.ad_id == ad_id
            )
        )
        return result.scalar_one_or_none() is not None