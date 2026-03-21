from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from api.dependencies import get_current_user
import hashlib
import hmac
from urllib.parse import parse_qs
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv('BOT_TOKEN')

@router.post("/verify")
async def verify_telegram_user(request: Request):
    """Проверяет данные пользователя из Telegram Mini App"""
    data = await request.json()
    init_data = data.get('initData')
    
    if not init_data:
        raise HTTPException(status_code=400, detail="No initData provided")
    
    parsed = parse_qs(init_data)
    received_hash = parsed.get('hash', [None])[0]
    
    if not received_hash:
        raise HTTPException(status_code=401, detail="Invalid data format")
    
    # Проверка подписи
    data_check = []
    for key in sorted(parsed.keys()):
        if key != 'hash':
            data_check.append(f"{key}={parsed[key][0]}")
    
    data_string = "\n".join(data_check)
    secret = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed = hmac.new(secret, data_string.encode(), hashlib.sha256).hexdigest()
    
    if computed != received_hash:
        logger.warning(f"Invalid signature: {computed} != {received_hash}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    logger.info("Telegram data verified successfully")
    return {"status": "ok"}

@router.get("/me")
async def get_current_user_info(user=Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return user