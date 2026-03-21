-- Создаём расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Устанавливаем таймзону
SET timezone = 'Europe/Moscow';

-- Создаём схему (опционально)
-- CREATE SCHEMA IF NOT EXISTS auto_ads;

-- Комментарии к таблицам будут созданы через миграции

-- Добавляем администратора (раскомментировать при необходимости)
-- INSERT INTO users (telegram_id, username, first_name, is_admin) 
-- VALUES (123456789, 'admin', 'Admin', true) 
-- ON CONFLICT (telegram_id) DO NOTHING;