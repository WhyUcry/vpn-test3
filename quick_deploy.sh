#!/bin/bash
# Быстрый деплой Dudonya VPN на новый сервер

set -e  # Выход при ошибке

echo "================================"
echo "Dudonya VPN - Автоматический деплой"
echo "Сервер: 213.189.222.68"
echo "Домен: dudonya.online"
echo "================================"
echo ""

# Проверка что мы на сервере
if [ "$EUID" -ne 0 ]; then
    echo "Запустите как root: sudo ./quick_deploy.sh"
    exit 1
fi

# Шаг 1: Обновление системы
echo "📦 Шаг 1: Обновление системы..."
apt update -qq && apt upgrade -y -qq

# Шаг 2: Установка Docker
echo ""
echo "🐳 Шаг 2: Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker уже установлен"
fi

# Установка docker compose plugin
if ! docker compose version &> /dev/null; then
    apt install docker-compose-plugin -y
fi

docker --version
docker compose version

# Шаг 3: Настройка Firewall
echo ""
echo "🔥 Шаг 3: Настройка Firewall..."
apt install ufw -y -qq
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
echo "Firewall настроен:"
ufw status verbose

# Шаг 4: Создание структуры
echo ""
echo "📁 Шаг 4: Создание структуры проекта..."
cd ~
if [ -d "dudonya-vpn" ]; then
    echo "Директория dudonya-vpn уже существует"
    echo "Переименовываю в dudonya-vpn.backup..."
    mv dudonya-vpn dudonya-vpn.backup.$(date +%Y%m%d_%H%M%S)
fi

mkdir -p dudonya-vpn
cd dudonya-vpn
mkdir -p configs data logs

echo ""
echo "================================"
echo "✅ Подготовка завершена!"
echo "================================"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Загрузите файлы проекта на сервер:"
echo "   scp -r * root@213.189.222.68:~/dudonya-vpn/"
echo ""
echo "2. Настройте .env файл:"
echo "   cd ~/dudonya-vpn"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "3. Инициализируйте БД и запустите:"
echo "   docker compose run --rm backend python scripts/init_db.py"
echo "   docker compose up -d"
echo ""
echo "4. Проверьте работу:"
echo "   docker compose ps"
echo "   curl http://localhost:8000/health"
echo ""
echo "📖 Полная инструкция: ~/dudonya-vpn/DEPLOY_NEW_SERVER.md"
echo ""
