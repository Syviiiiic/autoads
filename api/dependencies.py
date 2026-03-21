from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.queries import UserQueries
import hashlib
import hmac
import json
from urllib.parse import parse_qs
import os
import logging

logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Получить текущего пользователя из initData Telegram"""
    init_data = request.headers.get('X-Telegram-Init-Data')
    
    if not init_data:
        logger.warning("No init data in request")
        raise HTTPException(status_code=401, detail="No init data")
    
    # Проверка подписи Telegram
    parsed = parse_qs(init_data)
    received_hash = parsed.get('hash', [None])[0]
    
    if not received_hash:
        logger.warning("No hash in init data")
        raise HTTPException(status_code=401, detail="Invalid data")
    
    # Удаляем hash для проверки
    data_check = []
    for key in sorted(parsed.keys()):
        if key != 'hash':
            data_check.append(f"{key}={parsed[key][0]}")
    
    data_string = "\n".join(data_check)
    secret = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed = hmac.new(secret, data_string.encode(), hashlib.sha256).hexdigest()
    
    if computed != received_hash:
        logger.warning(f"Invalid signature: computed={computed}, received={received_hash}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Получаем данные пользователя
    user_data = json.loads(parsed.get('user', ['{}'])[0])
    
    # Сохраняем или обновляем пользователя в БД
    user = await UserQueries.get_or_create_user(
        db,
        telegram_id=user_data.get('id'),
        username=user_data.get('username'),
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name')
    )
    
    logger.info(f"User authenticated: {user.telegram_id} ({user.username})")
    
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_admin
    }