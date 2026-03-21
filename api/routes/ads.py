from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import logging

from database.db import get_db
from database.queries import AdQueries
from api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

class AdCreate(BaseModel):
    brand: str
    model: str
    year: int
    price: int
    mileage: Optional[int] = 0
    engine_capacity: Optional[float] = 0.0
    engine_type: Optional[str] = "Не указан"
    transmission: Optional[str] = "Не указана"
    drive: Optional[str] = "Не указан"
    color: Optional[str] = "Не указан"
    description: Optional[str] = ""
    photos: List[str] = []

class AdUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[int] = None
    mileage: Optional[int] = None
    engine_capacity: Optional[float] = None
    engine_type: Optional[str] = None
    transmission: Optional[str] = None
    drive: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AdResponse(BaseModel):
    id: int
    brand: str
    model: str
    year: int
    price: int
    mileage: int
    engine_capacity: float
    engine_type: str
    transmission: str
    drive: str
    color: str
    description: str
    photos: List[str]
    is_active: bool
    views_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    owner: dict

@router.post("/", response_model=dict)
async def create_ad(
    ad_data: AdCreate,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новое объявление"""
    try:
        ad = await AdQueries.create_ad(
            db,
            user_id=user['id'],
            ad_data=ad_data.dict()
        )
        logger.info(f"Ad created: {ad.id} by user {user['id']}")
        return {"id": ad.id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating ad: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ad")

@router.get("/", response_model=dict)
async def get_ads(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    brand: Optional[str] = None,
    model: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список объявлений с фильтрацией"""
    filters = {
        'brand': brand,
        'model': model,
        'price_min': price_min,
        'price_max': price_max,
        'year_min': year_min,
        'year_max': year_max
    }
    
    # Удаляем пустые фильтры
    filters = {k: v for k, v in filters.items() if v is not None and v != ''}
    
    try:
        ads = await AdQueries.get_ads(
            db,
            filters=filters,
            limit=limit,
            offset=(page-1)*limit
        )
        
        total = await AdQueries.count_ads(db, filters)
        
        items = []
        for ad in ads:
            items.append({
                "id": ad.id,
                "brand": ad.brand,
                "model": ad.model,
                "year": ad.year,
                "price": ad.price,
                "mileage": ad.mileage,
                "engine_type": ad.engine_type,
                "transmission": ad.transmission,
                "photos": json.loads(ad.photos) if ad.photos else [],
                "views_count": ad.views_count
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        logger.error(f"Error getting ads: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ads")

@router.get("/{ad_id}", response_model=dict)
async def get_ad(
    ad_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить объявление по ID"""
    try:
        ad = await AdQueries.get_ad_by_id(db, ad_id)
        if not ad:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        # Увеличиваем счётчик просмотров
        await AdQueries.increment_views(db, ad_id)
        
        return {
            "id": ad.id,
            "brand": ad.brand,
            "model": ad.model,
            "year": ad.year,
            "price": ad.price,
            "mileage": ad.mileage,
            "engine_capacity": ad.engine_capacity,
            "engine_type": ad.engine_type,
            "transmission": ad.transmission,
            "drive": ad.drive,
            "color": ad.color,
            "description": ad.description,
            "photos": json.loads(ad.photos) if ad.photos else [],
            "views_count": ad.views_count + 1,
            "created_at": ad.created_at,
            "owner": {
                "id": ad.owner.id,
                "telegram_id": ad.owner.telegram_id,
                "username": ad.owner.username,
                "first_name": ad.owner.first_name,
                "last_name": ad.owner.last_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ad {ad_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ad")

@router.put("/{ad_id}", response_model=dict)
async def update_ad(
    ad_id: int,
    ad_data: AdUpdate,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить объявление (только своё)"""
    try:
        ad = await AdQueries.get_ad_by_id(db, ad_id)
        if not ad:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        if ad.user_id != user['id'] and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Not your ad")
        
        update_data = {k: v for k, v in ad_data.dict().items() if v is not None}
        
        if 'photos' in update_data and isinstance(update_data['photos'], list):
            update_data['photos'] = json.dumps(update_data['photos'])
        
        success = await AdQueries.update_ad(db, ad_id, **update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update ad")
        
        logger.info(f"Ad {ad_id} updated by user {user['id']}")
        return {"status": "updated", "id": ad_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ad {ad_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ad")

@router.delete("/{ad_id}", response_model=dict)
async def delete_ad(
    ad_id: int,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить объявление (только своё)"""
    try:
        ad = await AdQueries.get_ad_by_id(db, ad_id)
        if not ad:
            raise HTTPException(status_code=404, detail="Ad not found")
        
        if ad.user_id != user['id'] and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Not your ad")
        
        success = await AdQueries.delete_ad(db, ad_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete ad")
        
        logger.info(f"Ad {ad_id} deleted by user {user['id']}")
        return {"status": "deleted", "id": ad_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ad {ad_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete ad")

@router.get("/user/{user_id}", response_model=List[dict])
async def get_user_ads(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить объявления пользователя"""
    try:
        ads = await AdQueries.get_user_ads(db, user_id)
        
        result = []
        for ad in ads:
            result.append({
                "id": ad.id,
                "brand": ad.brand,
                "model": ad.model,
                "year": ad.year,
                "price": ad.price,
                "mileage": ad.mileage,
                "engine_type": ad.engine_type,
                "transmission": ad.transmission,
                "photos": json.loads(ad.photos) if ad.photos else [],
                "is_active": ad.is_active,
                "views_count": ad.views_count,
                "created_at": ad.created_at
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting user ads: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user ads")