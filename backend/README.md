# Dudonya VPN Backend

Backend сервис для системы продажи VPN-подписок через Telegram-бота.

## Возможности

- 🔐 Генерация подписок с уникальными токенами
- 📱 Мягкий лимит устройств (1-5 устройств на подписку)
- 🔄 Стабильные UUID между запросами
- 📊 Поддержка двух режимов конфигов:
  - **Шаблонный** — с плейсхолдерами `{{UUID}}`, `{{DEVICE_ID}}`, `{{SHORT_ID}}`
  - **Статический** — готовые конфиги без подстановки
- ⚡ Rate limiting (10 req/min)
- 🌐 Совместимость с Happ, v2rayNG, Streisand, Hiddify, Shadowrocket

## Технологии

- Python 3.11+
- FastAPI + uvicorn
- SQLAlchemy (SQLite/PostgreSQL)
- Pydantic v2
- Loguru

## Установка (разработка)

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
cd backend
pip install -r requirements.txt
```

3. Создайте `.env` файл (на основе `.env.example`):
```bash
cp .env.example .env
# Отредактируйте .env
```

4. Инициализируйте базу данных:
```bash
python scripts/init_db.py --test-data
```

5. Запустите backend:
```bash
python backend/main.py
```

Сервер запустится на `http://localhost:8000`

## API Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### GET /sub/{token}
Получить подписку по токену.

**Headers (ответ):**
- `profile-title: Дудоня VPN`
- `profile-update-interval: 12`
- `subscription-userinfo: upload=0; download=0; total=0; expire=<unix_ts>`
- `Content-Type: text/plain; charset=utf-8`
- `Cache-Control: no-store`

**Response:**
- 200: Base64-encoded subscription (или plain text для WireGuard)
- 403: Подписка истекла или неактивна
- 404: Подписка не найдена

**Rate limit:** 10 запросов/минуту на IP

### POST /sub/{token}/rotate
Ротация UUID устройств (админ-эндпоинт).

**Response:**
```json
{
  "success": true,
  "message": "Rotated 3 device slots",
  "rotated_slots": [1, 2, 3]
}
```

## Конфигурация устройств

### Шаблонный режим (рекомендуется)

Создайте конфиг с плейсхолдерами в `configs/`:

```
vless://{{UUID}}@server.example.com:443?type=tcp&security=tls#Dudonya-{{SHORT_ID}}
```

Поддерживаемые плейсхолдеры:
- `{{UUID}}` — уникальный UUID устройства (стабильный)
- `{{DEVICE_ID}}` — ID устройства (алиас для UUID)
- `{{SHORT_ID}}` — короткий ID (8 символов)

### Статический режим

Положите готовые конфиги в `configs/`:

```
vless://abc123@server1.example.com:443?type=tcp&security=tls#Server1
ss://base64@server2.example.com:8388#Server2
```

Backend автоматически вернет первые N конфигов (по количеству устройств).

## Тестирование

```bash
cd tests
pip install -r requirements.txt
pytest test_subscription.py -v
```

Тесты проверяют:
- ✅ Корректность заголовков (profile-title с кириллицей)
- ✅ Количество конфигов = device_limit
- ✅ Стабильность UUID между запросами
- ✅ Обработку истекших/несуществующих подписок
- ✅ Rate limiting

## База данных

### Модели

**users**
- id, telegram_id (unique), username, created_at

**subscriptions**
- id, user_id, token (UUID), status, base_devices, extra_devices, created_at, expires_at

**device_slots**
- id, subscription_id, slot_index, uuid, short_id, created_at

**payments**
- id, user_id, amount, currency, provider, purpose, provider_payment_id, status, created_at, paid_at

**pending_payments**
- id, order_id, idempotency_key, user_id, amount, currency, purpose, provider, created_at, expires_at

### Слоты устройств

- Каждая подписка имеет `base_devices` (базовое кол-во) + `extra_devices` (докупленные)
- Максимум `MAX_DEVICES` (по умолчанию 5)
- При создании подписки генерируются слоты с уникальными UUID
- UUID стабильны — один и тот же слот всегда возвращает один и тот же UUID
- При продлении подписки UUID НЕ меняются (устройства продолжают работать)

## Логирование

Логи пишутся в:
- `stderr` — уровень INFO+ с цветным форматированием
- `logs/backend_YYYY-MM-DD.log` — все логи (DEBUG+), ротация ежедневно, хранение 30 дней

Токены логируются в усеченном виде (`token[:8]...`) для безопасности.

## Переменные окружения

См. `.env.example` для полного списка.

Основные:
- `DATABASE_URL` — URL базы данных
- `CONFIGS_DIR` — путь к конфигам
- `BASE_DEVICES` — базовое кол-во устройств (по умолчанию 1)
- `MAX_DEVICES` — максимум устройств (по умолчанию 5)

## Production Deploy

См. основной README в корне проекта для инструкций по развертыванию с Docker Compose.

## Лицензия

Proprietary - Dudonya VPN
