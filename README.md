# Дудоня VPN — Система продажи VPN-подписок

Полнофункциональная система продажи VPN-подписок через Telegram-бота с выдачей subscription-ссылок, совместимых с Happ VPN, v2rayNG, Streisand, Hiddify, Shadowrocket.

## 🚀 Возможности

- 📱 **Telegram-бот** с полным UI (aiogram 3.x)
- 💳 **2 платежных провайдера**: CryptoBot, Freekassa
- 🔐 **Мягкий лимит устройств** (1-5 на подписку)
- 📊 **Subscription API** с правильными заголовками
- 🔄 **Стабильные UUID** между запросами
- 🌐 **JSON конфиги** с поддержкой шаблонов `{{UUID}}`, `{{SHORT_ID}}`
- 🐳 **Docker Compose** с автоматическим SSL (Caddy)
- 🚀 **Автоматический деплой** через GitHub Actions
- 📖 **Подробные инструкции** для 5 VPN-клиентов

## 📂 Структура проекта

```
vpn-test3/
├── configs/                    # Ваши VPN-конфиги (JSON)
│   └── servers.json           # Пример с плейсхолдерами
├── backend/                   # FastAPI backend
│   ├── main.py               # API endpoints
│   ├── subscription.py       # Генерация подписок
│   ├── slot_generator.py     # UUID для устройств
│   ├── models.py             # SQLAlchemy модели
│   └── ...
├── bot/                       # Telegram-бот
│   ├── main.py               # Точка входа
│   ├── handlers.py           # Обработчики команд
│   ├── keyboards.py          # Клавиатуры
│   ├── texts.py              # Тексты и инструкции
│   └── payments/             # Платежные провайдеры
├── scripts/
│   └── init_db.py            # Инициализация БД
├── tests/
│   └── test_subscription.py  # Тесты
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.bot
├── Caddyfile                 # Caddy config (reverse proxy + SSL)
└── .env                      # Конфигурация (создать из .env.example)
```

## 🛠 Технологии

**Backend:**
- Python 3.11+
- FastAPI + uvicorn
- SQLAlchemy (SQLite/PostgreSQL)
- Pydantic v2
- Loguru

**Bot:**
- aiogram 3.x
- CryptoBot API
- Freekassa API

**Инфраструктура:**
- Docker + Docker Compose
- Caddy (автоматический Let's Encrypt)

## 📋 Требования

- Ubuntu 22.04 (или Debian-based дистрибутив)
- Docker 24.0+
- Docker Compose v2+
- Доменное имя с настроенным DNS
- Порты 80, 443 открыты

## 🚀 Быстрый старт (разработка)

1. Клонируйте репозиторий:
```bash
git clone <repo-url>
cd vpn-test3
```

2. Создайте `.env`:
```bash
cp .env.example .env
# Отредактируйте .env — укажите токены, цены, домен
```

3. Создайте конфиги в `configs/`:
```bash
# См. раздел "Конфигурация VPN-серверов" ниже
```

4. Инициализируйте БД:
```bash
python scripts/init_db.py --test-data
```

5. Запустите backend:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

6. Запустите бота (в отдельном терминале):
```bash
cd bot
pip install -r requirements.txt
python main.py
```

Backend: `http://localhost:8000`  
Бо��: работает через Telegram polling

## 🌐 Production Deploy

📖 **См. инструкцию по деплою:** [DEPLOY.md](DEPLOY.md)

**Возможности:**
- ✅ Ручной деплой на сервер
- ✅ Автоматический деплой через GitHub Actions
- ✅ Пошаговые инструкции с чек-листом

### Шаг 1: Подготовка сервера

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Установите Docker Compose v2
sudo apt install docker-compose-plugin -y

# Проверьте версии
docker --version
docker compose version
```

### Шаг 2: Настройка DNS

Добавьте A-запись для вашего домена:

```
Тип    Имя                  Значение
A      vpn.example.com      <IP вашего сервера>
```

Проверьте DNS:
```bash
dig +short vpn.example.com
# Должен вернуть IP вашего сервера
```

### Шаг 3: Настройка firewall (ufw)

```bash
# Установите ufw (если не установлен)
sudo apt install ufw -y

# Разрешите SSH (ВАЖНО!)
sudo ufw allow 22/tcp

# Разрешите HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включите firewall
sudo ufw enable

# Проверьте статус
sudo ufw status
```

### Шаг 4: Клонирование проекта

```bash
cd /opt
sudo git clone <repo-url> dudonya-vpn
cd dudonya-vpn
sudo chown -R $USER:$USER .
```

### Шаг 5: Конфигурация

#### 5.1. Создайте `.env`

```bash
cp .env.example .env
nano .env
```

**Обязательно заполните:**
```env
# Telegram
BOT_TOKEN=1234567890:AAAA...           # От @BotFather
ADMIN_ID=123456789                     # Ваш Telegram ID

# Domain
DOMAIN=https://vpn.example.com         # Ваш домен

# Database
DATABASE_URL=sqlite:///data/vpn.db     # Или Postgres

# Pricing
PRICE_1M=199
PRICE_3M=499
PRICE_12M=1499
CURRENCY=RUB

# Devices
BASE_DEVICES=1
MAX_DEVICES=5
PRICE_PER_DEVICE=99

# Payment providers (хотя бы один)
CRYPTOBOT_ENABLED=true
CRYPTOBOT_TOKEN=<ваш токен>
CRYPTOBOT_ASSET=USDT

FREEKASSA_ENABLED=true
FREEKASSA_SHOP_ID=<ваш shop_id>
FREEKASSA_SECRET_WORD_1=<secret_word_1>
FREEKASSA_SECRET_WORD_2=<secret_word_2>
FREEKASSA_API_KEY=<api_key>
```

#### 5.2. Обновите Caddyfile

```bash
nano Caddyfile
```

Замените `vpn.example.com` на ваш реальный домен и `admin@example.com` на ваш email.

#### 5.3. Создайте директории

```bash
mkdir -p data logs configs
chmod 755 data logs configs
```

### Шаг 6: Конфигурация VPN-серверов

Создайте `configs/servers.json` с вашими VPN-конфигами:

**Формат 1: С плейсхолдерами (рекомендуется)**
```json
{
  "configs": [
    "vless://{{UUID}}@server1.example.com:443?type=tcp&security=tls&sni=server1.example.com&fp=chrome#Dudonya-VPN-{{SHORT_ID}}",
    "vmess://{{UUID}}@server2.example.com:443?type=ws&security=tls&path=/ws#Dudonya-VPN-Slot{{SHORT_ID}}"
  ]
}
```

**Формат 2: Статические ссылки**
```json
{
  "configs": [
    "vless://abc123...@server1.example.com:443?type=tcp#Server1",
    "ss://base64...@server2.example.com:8388#Server2"
  ]
}
```

**Поддерживаемые плейсхолдеры:**
- `{{UUID}}` — уникальный UUID устройства (стабильный между запросами)
- `{{DEVICE_ID}}` — алиас для UUID
- `{{SHORT_ID}}` — короткий ID (8 символов)

### Шаг 7: Инициализация базы данных

```bash
# Инициализация БД (создание таблиц)
docker compose run --rm backend python scripts/init_db.py

# Или с тестовыми данными
docker compose run --rm backend python scripts/init_db.py --test-data
```

### Шаг 8: Запуск сервисов

```bash
# Запустите все сервисы
docker compose up -d

# Проверьте статус
docker compose ps

# Просмотрите логи
docker compose logs -f

# Или отдельно
docker compose logs -f backend
docker compose logs -f bot
docker compose logs -f caddy
```

**Ожидаемый вывод:**
```
✔ Container dudonya-backend   Started
✔ Container dudonya-bot        Started
✔ Container dudonya-caddy      Started
```

### Шаг 9: Проверка работы

#### 9.1. Проверьте backend

```bash
curl https://vpn.example.com/health
# Ожидается: {"status":"ok","timestamp":"...","version":"1.0.0"}
```

#### 9.2. Проверьте бота

Откройте Telegram → найдите вашего бота → отправьте `/start`

Должно появиться приветственное сообщение с кнопками.

#### 9.3. Проверьте SSL

```bash
curl -I https://vpn.example.com
# Должен вернуть 200 OK с заголовками
```

Откройте в браузере: `https://vpn.example.com/health`

## 📖 Использование

### Пользовательские команды (Telegram)

- `/start` — Главное меню
- Кнопки:
  - 💰 Купить подписку
  - 📱 Моя подписка
  - ➕ Докупить устройство
  - 📖 Как подключить
  - 💬 Поддержка

### Админ-команды (Telegram)

- `/stats` — Статистика (пользователи, подписки, выручка)
- `/grant <telegram_id> <days> [devices]` — Выдать подписку
- `/revoke <telegram_id>` — Отозвать подп��ску
- `/broadcast <текст>` — Рассылка всем пользователям

**Пример:**
```
/grant 123456789 30 2
# Выдать подписку пользователю 123456789 на 30 дней с 2 устройствами
```

## 🔗 API Endpoints

### GET /health
Health check.

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
```
profile-title: Дудоня VPN
profile-update-interval: 12
subscription-userinfo: upload=0; download=0; total=0; expire=1234567890
Content-Type: text/plain; charset=utf-8
Cache-Control: no-store
```

**Response:** Base64-encoded subscription (или plain text для WireGuard)

**Rate limit:** 10 req/min на IP

### POST /sub/{token}/rotate
Ротация UUID устройств (админ).

## 🧪 Тестирование

```bash
cd tests
pip install -r requirements.txt
pytest test_subscription.py -v
```

**Проверяемые аспекты:**
- ✅ Корректность заголовков (profile-title с кириллицей)
- ✅ Количество конфигов = device_limit
- ✅ Стабильность UUID между запросами
- ✅ Обработка истекших/несуществующих подписок
- ✅ Rate limiting

## 📱 Инструкции для клиентов

Пользователи получают ссылку вида: `https://vpn.example.com/sub/<token>`

### Happ VPN
1. Установите Happ (happ.su)
2. «+» → «Импорт подписки»
3. Вставьте ссылку
4. Выберите сервер → «Подключить»

### v2rayNG (Android)
1. Меню → «Группы» → «+» → «Импорт из буфера»
2. Вставьте ссылку → «Сохранить»
3. Обновите группу (⟳)
4. Выберите сервер → ▶

(См. полные инструкции в боте)

## 🔧 Обслуживание

### Просмотр логов

```bash
# Все логи
docker compose logs -f

# Backend
docker compose logs -f backend

# Bot
docker compose logs -f bot

# Логи на диске
tail -f logs/backend_*.log
tail -f logs/bot_*.log
```

### Остановка/перезапуск

```bash
# Остановить все
docker compose down

# Перезапустить
docker compose restart

# Перезапустить конкретный сервис
docker compose restart backend
docker compose restart bot
```

### Обновление

```bash
# Получите изменения
git pull

# Пересоберите и перезапустите
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Бэкап базы данных

```bash
# SQLite
cp data/vpn.db data/vpn_backup_$(date +%Y%m%d).db

# Или автоматический бэкап (cron)
crontab -e
# Добавьте:
0 3 * * * cp /opt/dudonya-vpn/data/vpn.db /opt/dudonya-vpn/data/backup_$(date +\%Y\%m\%d).db
```

## ⚠️ Troubleshooting

### Проблема: Бот не отвечает

**Решение:**
```bash
# Проверьте статус
docker compose ps

# Проверьте логи
docker compose logs bot

# Убедитесь, что BOT_TOKEN правильный
grep BOT_TOKEN .env
```

### Проблема: Ошибка SSL/TLS

**Решение:**
```bash
# Проверьте DNS
dig +short vpn.example.com

# Проверьте логи Caddy
docker compose logs caddy

# Перезапустите Caddy
docker compose restart caddy
```

### Проблема: Подписка не работает в Happ

**Решение:**
1. Проверьте формат конфигов в `configs/servers.json`
2. Убедитесь, что заголовок `profile-title: Дудоня VPN` присутствует:
```bash
curl -I https://vpn.example.com/sub/<token>
```
3. Проверьте base64-encoding (должен быть стандартный, не url-safe)

### Проблема: Платежи не проходят

**Решение:**
1. Проверьте токены в `.env`
2. Проверьте логи бота на ошибки API
3. Убедитесь, что webhook URL настроены в платежных системах:
   - CryptoBot: настраивается через `paid_btn_url`
   - Freekassa: `https://your-domain.com/webhook/freekassa`

## 📊 Мониторинг

### Простой мониторинг

```bash
# Проверка каждые 5 минут
watch -n 300 'curl -s https://vpn.example.com/health | jq'

# Или добавьте в cron
*/5 * * * * curl -s https://vpn.example.com/health || echo "Backend down!" | mail -s "Alert" admin@example.com
```

### Uptime Kuma (рекомендуется)

```bash
# Добавьте в docker-compose.yml
uptime-kuma:
  image: louislam/uptime-kuma:1
  container_name: uptime-kuma
  volumes:
    - uptime-kuma:/app/data
  ports:
    - "3001:3001"
  restart: unless-stopped
```

## 🔒 Безопасность

- ✅ Секреты только в `.env` (не коммитьте!)
- ✅ Rate limiting на API
- ✅ HTTPS через Caddy (автоматический Let's Encrypt)
- ✅ Идемпотентность webhook
- ✅ Проверка подписей (YooKassa IP, Robokassa MD5)
- ✅ Токены логируются усеченно (`token[:8]...`)

## 📝 Чек-лист перед запуском

- [ ] DNS настроен и резолвится
- [ ] `.env` заполнен (все токены, цены, домен)
- [ ] `Caddyfile` обновлен (ваш домен и email)
- [ ] `configs/servers.json` создан с вашими VPN-конфигами
- [ ] Порты 80, 443 открыты (ufw/iptables)
- [ ] База данных инициализирована (`init_db.py`)
- [ ] Docker Compose запущен (`docker compose up -d`)
- [ ] Backend отвечает на `/health`
- [ ] Бот отвечает на `/start` в Telegram
- [ ] SSL-сертификат получен (проверьте браузером)
- [ ] Тестовая покупка прошла успешно
- [ ] Подписка открывается в Happ/v2rayNG

## 🎯 Production Tips

1. **PostgreSQL вместо SQLite** (для высоких нагрузок):
```env
DATABASE_URL=postgresql://user:pass@localhost/dudonya_vpn
```

2. **Webhook вместо polling** для бота (быстрее):
```python
# bot/main.py
await dp.start_webhook(bot, webhook_url=f"{DOMAIN}/webhook")
```

3. **Регулярные бэкапы БД** (cron)

4. **Мониторинг** (Uptime Kuma, Prometheus)

5. **Логирование в Loki/ELK** (для продакшна)

## 📄 Лицензия

Proprietary — Dudonya VPN

## 🙏 Поддержка

Email: support@dudonya-vpn.com  
Telegram: @dudonya_support

---

**Успешного запуска! 🚀**
