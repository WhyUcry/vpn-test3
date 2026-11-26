# Исправления для деплоя

## Что исправлено:

### 1. SQLAlchemy ошибка с `metadata`
**Проблема:** `metadata` — зарезервированное слово в SQLAlchemy
**Решение:** Переименовано в `extra_data` в модели Payment

### 2. Конфликт версий pydantic
**Проблема:** aiogram 3.4.1 требует pydantic<2.6, но было 2.6.0
**Решение:** Понижена версия до pydantic==2.5.3

### 3. Docker Compose warning
**Проблема:** `version: '3.8'` устарел
**Решение:** Удалена строка version из docker-compose.yml

## Команды для применения исправлений:

```bash
# На сервере
cd ~/vpn-test3

# Пересоберите образы
docker compose down
docker compose build --no-cache

# Инициализируйте БД
docker compose run --rm backend python scripts/init_db.py

# Запустите
docker compose up -d

# Проверьте
docker compose ps
docker compose logs -f
```

## Проверка работы:

```bash
# 1. Backend health
curl https://dudonya.online/health

# 2. Логи backend
docker compose logs backend | tail -20

# 3. Логи bot
docker compose logs bot | tail -20

# 4. Статус контейнеров
docker compose ps
```

Если всё ОК — увидите:
- ✅ Backend: "Starting Dudonya VPN Backend..."
- ✅ Bot: "Bot started, polling for updates..."
- ✅ Caddy: SSL сертификат получен
