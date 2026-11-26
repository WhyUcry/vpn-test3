#!/bin/bash

echo "=== Применение исправлений для Dudonya VPN ==="
echo ""

# Остановить контейнеры
echo "1. Останавливаем контейнеры..."
docker compose down

# Очистить старые образы
echo ""
echo "2. Удаляем старые образы..."
docker compose rm -f
docker image prune -f

# Пересобрать с нуля
echo ""
echo "3. Пересобираем образы (это займет ~2 минуты)..."
docker compose build --no-cache

# Инициализировать БД
echo ""
echo "4. Инициализируем базу данных..."
docker compose run --rm backend python scripts/init_db.py

# Запустить все сервисы
echo ""
echo "5. Запускаем все сервисы..."
docker compose up -d

# Показать статус
echo ""
echo "6. Статус контейнеров:"
docker compose ps

echo ""
echo "=== Готово! ==="
echo ""
echo "Проверьте логи:"
echo "  docker compose logs -f backend"
echo "  docker compose logs -f bot"
echo ""
echo "Проверьте health:"
echo "  curl https://dudonya.online/health"
