#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Запуск Auto Ads Bot${NC}"
echo -e "${GREEN}========================================${NC}"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ Файл .env не найден. Создаю из .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠ Отредактируйте .env и добавьте BOT_TOKEN${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example не найден${NC}"
        exit 1
    fi
fi

# Создание необходимых директорий
echo -e "${BLUE}📁 Проверка директорий...${NC}"

if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "  ✅ Создана директория: ${GREEN}logs/${NC}"
else
    echo -e "  ✅ Директория уже существует: ${BLUE}logs/${NC}"
fi

if [ ! -d "docker/postgres/init" ]; then
    mkdir -p docker/postgres/init
    echo -e "  ✅ Создана директория: ${GREEN}docker/postgres/init/${NC}"
else
    echo -e "  ✅ Директория уже существует: ${BLUE}docker/postgres/init/${NC}"
fi

if [ ! -d "backups" ]; then
    mkdir -p backups
    echo -e "  ✅ Создана директория: ${GREEN}backups/${NC}"
else
    echo -e "  ✅ Директория уже существует: ${BLUE}backups/${NC}"
fi

# Проверка Docker
echo -e "${BLUE}🐳 Проверка Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен${NC}"
    echo -e "${YELLOW}Пожалуйста, установите Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi
echo -e "  ✅ Docker установлен: ${GREEN}$(docker --version | cut -d ' ' -f 3 | cut -d ',' -f 1)${NC}"

# Определение команды Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo -e "  ✅ Docker Compose установлен: ${GREEN}$(docker-compose --version | cut -d ' ' -f 3 | cut -d ',' -f 1)${NC}"
else
    COMPOSE_CMD="docker compose"
    echo -e "  ✅ Docker Compose установлен: ${GREEN}$(docker compose version --short)${NC}"
fi

# Остановка старых контейнеров
echo -e "${BLUE}🛑 Остановка старых контейнеров...${NC}"
$COMPOSE_CMD down 2>/dev/null

# Запуск контейнеров
echo -e "${BLUE}🚀 Запуск контейнеров...${NC}"
$COMPOSE_CMD up --build -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Система успешно запущена!${NC}"
    echo -e "\n${BLUE}📊 Статус контейнеров:${NC}"
    $COMPOSE_CMD ps
    
    echo -e "\n${BLUE}📝 Полезные команды:${NC}"
    echo -e "  • Просмотр логов бота: ${YELLOW}$COMPOSE_CMD logs -f bot${NC}"
    echo -e "  • Просмотр логов API:   ${YELLOW}$COMPOSE_CMD logs -f api${NC}"
    echo -e "  • Просмотр логов БД:    ${YELLOW}$COMPOSE_CMD logs -f postgres${NC}"
    echo -e "  • Остановка:            ${YELLOW}$COMPOSE_CMD down${NC}"
    echo -e "  • Перезапуск:           ${YELLOW}$COMPOSE_CMD restart${NC}"
    echo -e "  • Подключение к БД:     ${YELLOW}docker exec -it auto_ads_postgres psql -U \${DB_USER} -d \${DB_NAME}${NC}"
    
    echo -e "\n${YELLOW}📋 Логи бота (Ctrl+C для выхода):${NC}"
    $COMPOSE_CMD logs -f bot
else
    echo -e "${RED}❌ Ошибка при запуске контейнеров!${NC}"
    echo -e "${YELLOW}Проверьте логи: $COMPOSE_CMD logs${NC}"
    exit 1
fi