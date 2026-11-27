# 🚀 Полная инструкция по деплою Дудоня VPN

**Данные сервера:**
- IP: `213.189.222.68`
- Server ID: `vm_00b5552a`
- Домен: `dudonya.online`
- Репозиторий: `https://github.com/WhyUcry/vpn-test3`

---

## ✅ Шаг 1: Подключение к серверу

```bash
ssh root@213.189.222.68
```

После подключения проверьте систему:
```bash
# Проверка версии Ubuntu
cat /etc/os-release

# Проверка свободного места
df -h

# Проверка памяти
free -h
```

---

## ✅ Шаг 2: Установка Docker и Docker Compose

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка необходимых пакетов
apt install -y curl git ufw nano

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose v2
apt install -y docker-compose-plugin

# Проверка версий
docker --version
docker compose version

# Автозапуск Docker
systemctl enable docker
systemctl start docker
```

**Ожидаемый результат:**
```
Docker version 24.0+ 
Docker Compose version v2.20+
```

---

## ✅ Шаг 3: Настройка firewall

```bash
# Разрешаем SSH (ВАЖНО сделать это первым!)
ufw allow 22/tcp

# Разрешаем HTTP и HTTPS для Caddy
ufw allow 80/tcp
ufw allow 443/tcp

# Включаем firewall
ufw --force enable

# Проверяем статус
ufw status
```

**Ожидаемый результат:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## ✅ Шаг 4: Настройка DNS

**Перейдите в панель управления доменом `dudonya.online` и добавьте A-запись:**

```
Тип    Имя                  Значение            TTL
A      @                    213.189.222.68      300
A      www                  213.189.222.68      300
```

**Или только главный домен:**
```
Тип    Имя                  Значение            TTL
A      @                    213.189.222.68      300
```

**Проверка DNS (подождите 1-5 минут после добавления записи):**
```bash
# На сервере или локальном компьютере
dig +short dudonya.online

# Или
nslookup dudonya.online
```

**Ожидаемый результат:**
```
213.189.222.68
```

⚠️ **Важно:** Не переходите к следующему шагу, пока DNS не будет резолвиться правильно!

---

## ✅ Шаг 5: Клонирование проекта

```bash
# Переходим в /opt
cd /opt

# Останавливаем старый проект, если он есть
if [ -d "dudonya-vpn" ]; then
    cd dudonya-vpn
    docker compose down 2>/dev/null || true
    cd /opt
fi

# Удаляем старую директорию (если нужно)
rm -rf dudonya-vpn vpn-test3

# Клонируем проект
git clone https://github.com/WhyUcry/vpn-test3.git dudonya-vpn

# Переходим в директорию
cd dudonya-vpn

# Проверяем, что файлы на месте
ls -la
```

**Ожидаемый результат:**
```
backend/
bot/
configs/
scripts/
docker-compose.yml
Dockerfile.backend
Dockerfile.bot
Caddyfile
.env.example
README.md
...
```

---

## ✅ Шаг 6: Настройка .env

```bash
# Создаем .env из примера
cp .env.example .env

# Редактируем файл
nano .env
```

**Вставьте следующие данные (замените значения токенов на свои):**

```env
# Telegram Bot
BOT_TOKEN=ВАШ_ТОКЕН_ОТ_BOTFATHER
BOT_USERNAME=dudonyaVPN_bot
ADMIN_ID=852242429

# Domain and Backend
DOMAIN=https://dudonya.online
DATABASE_URL=sqlite:///data/vpn.db
CONFIGS_DIR=/app/configs

# Pricing (in rubles)
PRICE_1M=199
PRICE_3M=499
PRICE_12M=1499
CURRENCY=RUB

# Device limits
BASE_DEVICES=1
MAX_DEVICES=5
PRICE_PER_DEVICE=99

# CryptoBot (Crypto Pay API)
CRYPTOBOT_ENABLED=true
CRYPTOBOT_TOKEN=ВАШ_ТОКЕН_CRYPTOBOT
CRYPTOBOT_ASSET=USDT

# Freekassa (Фрикасса)
FREEKASSA_ENABLED=true
FREEKASSA_SHOP_ID=ВАШ_SHOP_ID
FREEKASSA_SECRET_WORD_1=ВАШ_SECRET_1
FREEKASSA_SECRET_WORD_2=ВАШ_SECRET_2
FREEKASSA_API_KEY=ВАШ_API_KEY

# Logging
LOG_LEVEL=INFO
```

**Где взять токены:**
1. **BOT_TOKEN**: Напишите @BotFather в Telegram → `/newbot` → следуйте инструкциям
2. **CRYPTOBOT_TOKEN**: Перейдите в @CryptoBot → Crypto Pay API → создайте приложение
3. **FREEKASSA**: Зарегистрируйтесь на https://freekassa.ru → Настройки → API

**Сохранение файла в nano:**
- `Ctrl + O` (сохранить)
- `Enter` (подтвердить)
- `Ctrl + X` (выйти)

---

## ✅ Шаг 7: Настройка Caddyfile

```bash
nano Caddyfile
```

**Замените содержимое на:**

```
{
    email admin@dudonya.online
}

dudonya.online {
    # Reverse proxy to backend
    reverse_proxy backend:8000

    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer-when-downgrade"
        -Server
    }

    # Rate limiting
    rate_limit {
        zone subscription {
            key {remote_host}
            events 100
            window 1m
        }
    }

    # Logs
    log {
        output file /data/access.log
        format json
    }

    # TLS (automatic Let's Encrypt)
    tls {
        protocols tls1.2 tls1.3
    }
}
```

**Сохраните:** `Ctrl + O`, `Enter`, `Ctrl + X`

---

## ✅ Шаг 8: Настройка VPN конфигов

У вас уже есть готовые конфиги в `configs/`:
- Белые списки 1.json, 2.json, 3.json
- Венгрия.json
- Россия.json
- Сша.json
- Франция.json
- Хельсинки.json

⚠️ **Важно:** Эти файлы — полные V2Ray/Xray конфиги, но backend ожидает простые subscription-ссылки!

### 🔄 Автоматическая конвертация (рекомендуется)

Используйте готовый скрипт для конвертации:

```bash
# Запустите конвертер
python3 scripts/convert_configs.py

# Проверьте результат
cat configs/servers.json | head -30
```

**Скрипт автоматически:**
- ✅ Извлечет VLESS/VMess настройки из всех конфигов
- ✅ Создаст subscription-ссылки с плейсхолдерами `{{UUID}}`
- ✅ Сгенерирует `configs/servers.json` в правильном формате

**Ожидаемый результат:**
```json
{
  "configs": [
    "vless://{{UUID}}@185.16.213.6:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=internity.ru&fp=qq&pbk=R_km...#🇷🇺Россия-{{SHORT_ID}}",
    "vless://{{UUID}}@...",
    ...
  ]
}
```

📖 **Подробная инструкция:** См. [CONFIGS_GUIDE.md](CONFIGS_GUIDE.md)

### 🛠 Альтернатива: Ручное создание

Если скрипт не работает или у вас есть готовые subscription-ссылки:

```bash
nano configs/servers.json
```

```json
{
  "configs": [
    "vless://{{UUID}}@your-server.com:443?type=tcp&security=reality&sni=server.com&fp=chrome&pbk=YOUR_KEY&sid=YOUR_ID#Server-{{SHORT_ID}}"
  ]
}
```

⚠️ **Важно:** Замените `your-server.com` и параметры на реальные!

---

## ✅ Шаг 9: Создание необходимых директорий

```bash
# Создаем директории для данных и логов
mkdir -p data logs

# Устанавливаем права доступа
chmod 755 data logs configs
```

---

## ✅ Шаг 10: Инициализация базы данных

```bash
# Инициализируем БД (создание таблиц)
docker compose run --rm backend python scripts/init_db.py

# Или с тестовыми данными (для проверки)
docker compose run --rm backend python scripts/init_db.py --test-data
```

**Ожидаемый результат:**
```
Pulling backend...
Creating database tables...
Database initialized successfully!
```

---

## ✅ Шаг 11: Запуск сервисов

```bash
# Собираем и запускаем все контейнеры
docker compose up -d

# Проверяем статус
docker compose ps
```

**Ожидаемый результат:**
```
NAME                IMAGE              STATUS         PORTS
dudonya-backend     vpn-test3-backend  Up (healthy)   8000/tcp
dudonya-bot         vpn-test3-bot      Up             
dudonya-caddy       caddy:2-alpine     Up             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

**Смотрим логи (ждем 2-3 минуты для получения SSL-сертификата):**
```bash
docker compose logs -f
```

Ожидайте сообщения:
- Backend: `Uvicorn running on http://0.0.0.0:8000`
- Bot: `Bot started successfully`
- Caddy: `certificate obtained successfully`

**Остановить просмотр логов:** `Ctrl + C`

---

## ✅ Шаг 12: Проверка работы

### 12.1. Проверка backend

```bash
# Локальная проверка
curl http://localhost:8000/health

# Через домен (подождите 2-3 минуты для SSL)
curl https://dudonya.online/health
```

**Ожидаемый результат:**
```json
{"status":"ok","timestamp":"2024-01-26T12:00:00","version":"1.0.0"}
```

### 12.2. Проверка SSL-сертификата

```bash
# Проверка SSL
curl -I https://dudonya.online/health
```

Должны увидеть статус `200 OK` и заголовки с `Content-Type: application/json`.

**Или откройте в браузере:**
```
https://dudonya.online/health
```

Должен быть зеленый замочек 🔒 (валидный SSL-сертификат).

### 12.3. Проверка бота

1. Откройте Telegram
2. Найдите бота: `@dudonyaVPN_bot`
3. Отправьте команду `/start`

**Ожидаемый результат:**
Бот должен ответить приветственным сообщением с кнопками:
- 💰 Купить подписку
- 📱 Моя подписка
- 📖 Как подключить
- 💬 Поддержка

### 12.4. Проверка админ-панели

Отправьте боту команду (от вашего Telegram ID):
```
/stats
```

Должна появиться статистика системы.

---

## ✅ Шаг 13: Настройка webhook в Freekassa

1. Войдите в панель Freekassa: https://freekassa.ru
2. Перейдите в **Настройки магазина**
3. Найдите поле **URL для результата (Result URL)**
4. Вставьте: `https://dudonya.online/webhook/freekassa`
5. Сохраните настройки

---

## ✅ Шаг 14: Тестовая покупка

1. Откройте бота `@dudonyaVPN_bot`
2. Нажмите **💰 Купить подписку**
3. Выберите тариф (например, 1 месяц - 199₽)
4. Выберите платежную систему
5. Оплатите тестовую сумму
6. Проверьте, что подписка активировалась

**Проверка подписки:**
```
📱 Моя подписка
```

Должна появиться ваша активная подписка с токеном.

---

## 🎉 Деплой завершен!

Ваш VPN-сервис работает по адресу: **https://dudonya.online**

---

## 🔄 Автоматический деплой через GitHub Actions (опционально)

### Шаг 1: Создание SSH-ключа на сервере

```bash
# На сервере (213.189.222.68)
ssh-keygen -t ed25519 -C "github-deploy-dudonya" -f ~/.ssh/github_deploy

# НЕ ВВОДИТЕ пароль (просто нажмите Enter дважды)

# Добавьте публичный ключ в authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

# Выведите приватный ключ (понадобится для GitHub)
cat ~/.ssh/github_deploy
```

**Скопируйте весь вывод команды** (от `-----BEGIN OPENSSH PRIVATE KEY-----` до `-----END OPENSSH PRIVATE KEY-----` включительно).

### Шаг 2: Добавление секретов в GitHub

1. Откройте: https://github.com/WhyUcry/vpn-test3/settings/secrets/actions
2. Нажмите **New repository secret**
3. Добавьте 5 секретов:

| Name | Value |
|------|-------|
| `SERVER_HOST` | `213.189.222.68` |
| `SERVER_USER` | `root` |
| `SSH_PRIVATE_KEY` | *Вставьте приватный ключ из предыдущего шага* |
| `SSH_PORT` | `22` |
| `DEPLOY_PATH` | `/opt/dudonya-vpn` |

### Шаг 3: Проверка GitHub Actions

Workflow уже настроен в `.github/workflows/deploy.yml`. Теперь при каждом `git push` проект будет автоматически деплоиться на сервер.

**Тест:**
```bash
# На локальном компьютере
echo "# Auto-deploy test" >> README.md
git add .
git commit -m "test: проверка автодеплоя"
git push origin main
```

Перейдите на GitHub → вкладка **Actions** → наблюдайте за процессом деплоя.

---

## 🔧 Полезные команды

### Просмотр логов
```bash
# Все логи в реальном времени
docker compose logs -f

# Только backend
docker compose logs -f backend

# Только bot
docker compose logs -f bot

# Только caddy
docker compose logs -f caddy

# Последние 100 строк
docker compose logs --tail=100

# Логи на диске
tail -f logs/backend_*.log
tail -f logs/bot_*.log
```

### Управление контейнерами
```bash
# Статус контейнеров
docker compose ps

# Перезапуск всех сервисов
docker compose restart

# Перезапуск конкретного сервиса
docker compose restart backend
docker compose restart bot

# Остановка
docker compose down

# Остановка и удаление volumes
docker compose down -v

# Пересборка без кеша
docker compose build --no-cache

# Пересборка и запуск
docker compose up -d --build
```

### Обновление с GitHub
```bash
cd /opt/dudonya-vpn

# Получить изменения
git pull origin main

# Пересобрать и перезапустить
docker compose down
docker compose build --no-cache
docker compose up -d

# Проверить
docker compose logs -f
```

### Работа с базой данных
```bash
# Бэкап базы данных
cp data/vpn.db data/vpn_backup_$(date +%Y%m%d_%H%M%S).db

# Восстановление из бэкапа
cp data/vpn_backup_20240126_120000.db data/vpn.db
docker compose restart backend bot

# Просмотр базы данных (требует sqlite3)
apt install sqlite3 -y
sqlite3 data/vpn.db "SELECT * FROM users LIMIT 10;"
sqlite3 data/vpn.db "SELECT * FROM subscriptions WHERE active = 1;"
```

### Проверка здоровья системы
```bash
# Использование диска
df -h

# Использование памяти
free -h

# Статистика Docker
docker stats

# Размер образов
docker images

# Очистка неиспользуемых образов
docker system prune -a
```

---

## ⚠️ Troubleshooting

### Проблема: Контейнеры не запускаются

**Решение:**
```bash
# Проверьте статус Docker
systemctl status docker

# Перезапустите Docker
systemctl restart docker

# Проверьте логи
docker compose logs

# Проверьте .env файл
cat .env | grep -v "^#" | grep -v "^$"
```

### Проблема: Порт 80 или 443 занят

**Решение:**
```bash
# Найдите процесс, занимающий порт
lsof -i :80
lsof -i :443

# Или
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Остановите nginx/apache, если они есть
systemctl stop nginx
systemctl stop apache2
systemctl disable nginx
systemctl disable apache2

# Перезапустите проект
docker compose down
docker compose up -d
```

### Проблема: SSL-сертификат не получен

**Решение:**
```bash
# Проверьте DNS
dig +short dudonya.online
# Должно вернуть: 213.189.222.68

# Проверьте firewall
ufw status
# Порты 80 и 443 должны быть открыты

# Проверьте логи Caddy
docker compose logs caddy | grep -i error
docker compose logs caddy | grep -i certificate

# Перезапустите Caddy
docker compose restart caddy

# Если не помогает, удалите данные Caddy и попробуйте снова
docker compose down
docker volume rm dudonya-vpn_caddy_data dudonya-vpn_caddy_config
docker compose up -d
```

### Проблема: Бот не отвечает

**Решение:**
```bash
# Проверьте статус контейнера
docker compose ps bot

# Проверьте логи бота
docker compose logs bot | tail -50

# Проверьте .env
grep BOT_TOKEN .env
grep ADMIN_ID .env

# Убедитесь, что BOT_TOKEN правильный
# Перезапустите бота
docker compose restart bot
```

### Проблема: Webhook не работает (оплата не проходит)

**Решение:**
```bash
# Проверьте backend логи
docker compose logs backend | grep webhook

# Проверьте доступность endpoint
curl https://dudonya.online/health

# Проверьте настройки в Freekassa
# URL должен быть: https://dudonya.online/webhook/freekassa

# Проверьте SECRET_WORD в .env
grep FREEKASSA .env

# Проверьте логи бота на ошибки платежей
docker compose logs bot | grep -i payment
docker compose logs bot | grep -i freekassa
```

### Проблема: Подписка не активируется после оплаты

**Решение:**
```bash
# Проверьте, что BOT_USERNAME указан в .env
grep BOT_USERNAME .env
# Должно быть: BOT_USERNAME=dudonyaVPN_bot (БЕЗ @)

# Проверьте логи обоих контейнеров
docker compose logs bot | grep -i "payment"
docker compose logs backend | grep -i "subscription"

# Перезапустите сервисы
docker compose restart
```

### Проблема: База данных повреждена

**Решение:**
```bash
# Остановите сервисы
docker compose down

# Создайте бэкап
cp data/vpn.db data/vpn.db.broken

# Проверьте целостность
sqlite3 data/vpn.db "PRAGMA integrity_check;"

# Если база повреждена, создайте новую
rm data/vpn.db
docker compose run --rm backend python scripts/init_db.py

# Запустите сервисы
docker compose up -d
```

---

## 📊 Мониторинг

### Простой мониторинг с curl

```bash
# Создайте скрипт
nano /root/check_dudonya.sh
```

```bash
#!/bin/bash
DOMAIN="https://dudonya.online"
TELEGRAM_BOT_TOKEN="ВАШ_ТОКЕН"
TELEGRAM_CHAT_ID="852242429"

if ! curl -sf "$DOMAIN/health" > /dev/null; then
    MESSAGE="🚨 Dudonya VPN не отвечает! Проверьте сервер."
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=$MESSAGE"
fi
```

```bash
# Сделайте скрипт исполняемым
chmod +x /root/check_dudonya.sh

# Добавьте в cron (проверка каждые 5 минут)
crontab -e
# Добавьте строку:
*/5 * * * * /root/check_dudonya.sh
```

### Мониторинг через Uptime Kuma (опционально)

```bash
# Добавьте в docker-compose.yml
nano docker-compose.yml

# В конец файла добавьте:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: dudonya-uptime
    volumes:
      - uptime-kuma:/app/data
    ports:
      - "3001:3001"
    restart: unless-stopped
    networks:
      - dudonya-net

# В секцию volumes добавьте:
  uptime-kuma:

# Перезапустите
docker compose up -d
```

Затем откройте: `http://213.189.222.68:3001`

---

## 🔒 Безопасность

### Смена SSH-порта (рекомендуется)

```bash
# Измените SSH порт
nano /etc/ssh/sshd_config

# Найдите строку #Port 22 и замените на:
Port 2222

# Сохраните и перезапустите SSH
systemctl restart sshd

# Обновите firewall
ufw allow 2222/tcp
ufw delete allow 22/tcp

# Теперь подключайтесь через новый порт
ssh -p 2222 root@213.189.222.68
```

### Автоматическое обновление системы

```bash
# Установите unattended-upgrades
apt install unattended-upgrades -y

# Настройте автообновление
dpkg-reconfigure -plow unattended-upgrades
```

### Регулярный бэкап

```bash
# Создайте скрипт бэкапа
nano /root/backup_dudonya.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
PROJECT_DIR="/opt/dudonya-vpn"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp $PROJECT_DIR/data/vpn.db $BACKUP_DIR/vpn_$DATE.db

# Бэкап .env
cp $PROJECT_DIR/.env $BACKUP_DIR/env_$DATE.txt

# Удалить старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.txt" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Сделайте скрипт исполняемым
chmod +x /root/backup_dudonya.sh

# Добавьте в cron (каждый день в 3:00)
crontab -e
# Добавьте:
0 3 * * * /root/backup_dudonya.sh
```

---

## 📋 Итоговый чек-лист

- [x] Сервер настроен (Docker, firewall)
- [x] DNS настроен и резолвится (dudonya.online → 213.189.222.68)
- [x] Проект клонирован в /opt/dudonya-vpn
- [x] .env настроен с токенами
- [x] Caddyfile обновлен с доменом dudonya.online
- [x] VPN-конфиги подготовлены в configs/servers.json
- [x] База данных инициализирована
- [x] Контейнеры запущены
- [x] Backend отвечает на https://dudonya.online/health
- [x] SSL-сертификат получен (зеленый замочек)
- [x] Бот @dudonyaVPN_bot отвечает на /start
- [x] Админ-команда /stats работает
- [x] Webhook настроен в Freekassa
- [x] Тестовая покупка прошла успешно
- [x] Подписка активировалась автоматически

---

## 📞 Поддержка

**Telegram:** @dudonya_support  
**Email:** support@dudonya.online

---

**🎉 Поздравляем! Дудоня VPN успешно развернут!**

Ваш сервис доступен по адресу: **https://dudonya.online**  
Бот работает: **@dudonyaVPN_bot**
