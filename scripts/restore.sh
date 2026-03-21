#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   Восстановление базы данных${NC}"
echo -e "${YELLOW}========================================${NC}"

if [ -z "$1" ]; then
    echo -e "${RED}❌ Укажите файл бэкапа для восстановления${NC}"
    echo -e "${BLUE}Использование: ./scripts/restore.sh backups/backup_20240315_120000.sql.gz${NC}"
    exit 1
fi

BACKUP_FILE=$1

# Проверяем существование файла
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Файл $BACKUP_FILE не найден${NC}"
    exit 1
fi

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

echo -e "${YELLOW}⚠ ВНИМАНИЕ: Это действие перезапишет текущую базу данных!${NC}"
echo -e "${YELLOW}Продолжить? (y/n)${NC}"
read -r confirm

if [[ ! "$confirm" =~ ^[YyДд]$ ]]; then
    echo -e "${BLUE}Операция отменена${NC}"
    exit 0
fi

# Распаковываем, если файл сжатый
if [[ $BACKUP_FILE == *.gz ]]; then
    echo -e "${BLUE}Распаковка бэкапа...${NC}"
    gunzip -c $BACKUP_FILE > /tmp/restore_temp.sql
    RESTORE_FILE=/tmp/restore_temp.sql
else
    RESTORE_FILE=$BACKUP_FILE
fi

# Восстанавливаем базу
echo -e "${BLUE}Восстановление базы данных...${NC}"
cat $RESTORE_FILE | docker exec -i auto_ads_postgres psql -U ${DB_USER:-autobot} -d ${DB_NAME:-auto_ads}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ База данных успешно восстановлена из $BACKUP_FILE${NC}"
else
    echo -e "${RED}❌ Ошибка при восстановлении${NC}"
    exit 1
fi

# Удаляем временный файл
rm -f /tmp/restore_temp.sql