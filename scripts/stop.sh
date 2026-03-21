#!/bin/bash

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   Остановка Auto Ads Bot${NC}"
echo -e "${YELLOW}========================================${NC}"

# Определение команды Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ Docker Compose не найден!${NC}"
    exit 1
fi

# Проверка запущенных контейнеров
RUNNING=$($COMPOSE_CMD ps --services --filter "status=running" 2>/dev/null)

if [ -z "$RUNNING" ]; then
    echo -e "${BLUE}ℹ Нет запущенных контейнеров${NC}"
else
    echo -e "${BLUE}Останавливаю контейнеры...${NC}"
    $COMPOSE_CMD down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Контейнеры остановлены${NC}"
    else
        echo -e "${RED}❌ Ошибка при остановке${NC}"
        exit 1
    fi
fi

# Спрашиваем про удаление данных
echo -e "${YELLOW}Удалить volume с данными БД? (y/n)${NC}"
echo -e "${RED}⚠ ВНИМАНИЕ: Все данные будут безвозвратно потеряны!${NC}"
read -r delete_volumes

if [[ "$delete_volumes" =~ ^[YyДд]$ ]]; then
    echo -e "${RED}Удаление volume...${NC}"
    $COMPOSE_CMD down -v
    echo -e "${GREEN}✅ Volume удалены${NC}"
fi

echo -e "${GREEN}✅ Готово!${NC}"