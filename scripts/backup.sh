#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Создание бэкапа базы данных${NC}"
echo -e "${BLUE}========================================${NC}"

# Создаём директорию для бэкапов
mkdir -p backups

# Получаем текущую дату
DATE=$(date +%Y%m%d_%H%M%S)

# Загружаем переменные из .env
if [ -f .env ]; then
    source .env
else
    echo -e "${RED}❌ Файл .env не найден${NC}"
    exit 1
fi

# Проверяем, запущен ли контейнер
if ! docker ps | grep -q auto_ads_postgres; then
    echo -e "${RED}❌ Контейнер PostgreSQL не запущен${NC}"
    exit 1
fi

# Создаём бэкап
echo -e "${BLUE}Создание бэкапа...${NC}"
docker exec auto_ads_postgres pg_dump -U ${DB_USER:-autobot} -d ${DB_NAME:-auto_ads} > backups/backup_$DATE.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Бэкап создан: backups/backup_$DATE.sql${NC}"
    
    # Сжимаем бэкап
    gzip backups/backup_$DATE.sql
    echo -e "${GREEN}✅ Бэкап сжат: backups/backup_$DATE.sql.gz${NC}"
    
    # Показываем размер
    SIZE=$(du -h backups/backup_$DATE.sql.gz | cut -f1)
    echo -e "${GREEN}📦 Размер: $SIZE${NC}"
else
    echo -e "${RED}❌ Ошибка при создании бэкапа${NC}"
    exit 1
fi