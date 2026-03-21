from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from database.db import get_db
from database.models import Ad
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db)
):
    """Автодополнение для поиска"""
    try:
        # Ищем по маркам
        brands_query = select(Ad.brand, func.count(Ad.id).label('count'))\
            .where(Ad.is_active == True)\
            .where(Ad.brand.ilike(f"%{query}%"))\
            .group_by(Ad.brand)\
            .order_by(func.count(Ad.id).desc())\
            .limit(5)
        
        # Ищем по моделям
        models_query = select(Ad.model, func.count(Ad.id).label('count'))\
            .where(Ad.is_active == True)\
            .where(Ad.model.ilike(f"%{query}%"))\
            .group_by(Ad.model)\
            .order_by(func.count(Ad.id).desc())\
            .limit(5)
        
        brands_result = await db.execute(brands_query)
        models_result = await db.execute(models_query)
        
        suggestions = []
        
        for brand, count in brands_result:
            suggestions.append({
                "type": "brand",
                "value": brand,
                "count": count
            })
        
        for model, count in models_result:
            suggestions.append({
                "type": "model",
                "value": model,
                "count": count
            })
        
        return suggestions
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return []

@router.get("/filters")
async def get_filter_options(db: AsyncSession = Depends(get_db)):
    """Получить доступные варианты для фильтров"""
    try:
        # Уникальные марки с количеством
        brands_query = select(Ad.brand, func.count(Ad.id).label('count'))\
            .where(Ad.is_active == True)\
            .group_by(Ad.brand)\
            .order_by(Ad.brand)
        
        # Диапазон цен
        price_range = await db.execute(
            select(
                func.min(Ad.price),
                func.max(Ad.price)
            ).where(Ad.is_active == True)
        )
        
        # Диапазон годов
        year_range = await db.execute(
            select(
                func.min(Ad.year),
                func.max(Ad.year)
            ).where(Ad.is_active == True)
        )
        
        brands_result = await db.execute(brands_query)
        price_min, price_max = price_range.one()
        year_min, year_max = year_range.one()
        
        return {
            "brands": [{"name": b, "count": c} for b, c in brands_result],
            "price": {
                "min": price_min or 0,
                "max": price_max or 10000000
            },
            "year": {
                "min": year_min or 1900,
                "max": year_max or 2026
            }
        }
    except Exception as e:
        logger.error(f"Error getting filters: {e}")
        return {
            "brands": [],
            "price": {"min": 0, "max": 10000000},
            "year": {"min": 1900, "max": 2026}
        }