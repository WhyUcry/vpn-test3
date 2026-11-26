# 🚀 Деплой Dudonya VPN на 213.189.222.68

## Информация о сервере
- **IP:** 213.189.222.68
- **Hostname:** vm_00b5552a
- **Домен:** dudonya.online
- **User:** root

---

## Шаг 1: Настройка DNS

### 1.1 В панели reg.ru обновите A-запись

Зайдите в панель управления доменом dudonya.online и обновите:

```
Тип    Имя              Значение
A      @                213.189.222.68
A      www              213.189.222.68
```

### 1.2 Проверьте DNS (может занять до 30 минут)

**На вашем компьютере:**
```bash
dig +short dudonya.online
# Должно вернуть: 213.189.222.68

nslookup dudonya.online
# Должно показать: 213.189.222.68
```

---

## Шаг 2: Подключение к серверу

```bash
ssh root@213.189.222.68
```

После подключения выполните:

```bash
# Проверьте систему
uname -a
cat /etc/os-release

# Обновите систему
apt update && apt upgrade -y
```

---

## Шаг 3: Установка Docker

```bash
# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Проверьте версию
docker --version
docker compose version

# Если docker compose не работает, установите плагин
apt install docker-compose-plugin -y
```

---

## Шаг 4: Настройка Firewall

```bash
# Установите UFW (если нет)
apt install ufw -y

# Настройте правила
ufw allow 22/tcp    # SSH (ВАЖНО!)
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# Включите firewall
ufw --force enable

# Проверьте статус
ufw status verbose
```

---

## Шаг 5: Создание структуры проекта

```bash
# Создайте директорию
mkdir -p ~/dudonya-vpn
cd ~/dudonya-vpn

# Создайте поддиректории
mkdir -p configs data logs backend bot bot/payments scripts tests
```

---

## Шаг 6: Загрузка файлов проекта

### Вариант А: Через SCP (с вашего компьютера)

**На вашем Windows компьютере откройте PowerShell:**

```powershell
cd "C:\Users\admin\OneDrive\Desktop\dudonya vpn\vpn-test3"

# Загрузите все файлы
scp -r * root@213.189.222.68:~/dudonya-vpn/
```

### Вариант Б: Через Git (если у вас есть репозиторий)

**На сервере:**
```bash
cd ~
git clone <ваш-репозиторий-url> dudonya-vpn
cd dudonya-vpn
```

### Вариант В: Поэтапная загрузка

**На Windows (PowerShell):**
```powershell
cd "C:\Users\admin\OneDrive\Desktop\dudonya vpn\vpn-test3"

# Backend
scp -r backend root@213.189.222.68:~/dudonya-vpn/

# Bot
scp -r bot root@213.189.222.68:~/dudonya-vpn/

# Configs
scp -r configs root@213.189.222.68:~/dudonya-vpn/

# Scripts
scp -r scripts root@213.189.222.68:~/dudonya-vpn/

# Docker файлы
scp docker-compose.yml root@213.189.222.68:~/dudonya-vpn/
scp Dockerfile.backend root@213.189.222.68:~/dudonya-vpn/
scp Dockerfile.bot root@213.189.222.68:~/dudonya-vpn/
scp Caddyfile root@213.189.222.68:~/dudonya-vpn/

# .env.example
scp .env.example root@213.189.222.68:~/dudonya-vpn/
```

---

## Шаг 7: Настройка .env файла

**На сервере:**

```bash
cd ~/dudonya-vpn

# Скопируйте шаблон
cp .env.example .env

# Отредактируйте
nano .env
```

**Вставьте и заполните:**

```env
# Telegram Bot
BOT_TOKEN=<ваш токен от @BotFather>
ADMIN_ID=<ваш Telegram ID>

# Domain
DOMAIN=https://dudonya.online

# Database
DATABASE_URL=sqlite:///data/vpn.db
CONFIGS_DIR=/app/configs

# Pricing
PRICE_1M=199
PRICE_3M=499
PRICE_12M=1499
CURRENCY=RUB

# Device limits
BASE_DEVICES=1
MAX_DEVICES=5
PRICE_PER_DEVICE=99

# CryptoBot
CRYPTOBOT_ENABLED=true
CRYPTOBOT_TOKEN=686392:AAnzKbWT4rYn6Yiy0xBVbpSyGA89wAaZWQj
CRYPTOBOT_ASSET=USDT

# Freekassa
FREEKASSA_ENABLED=true
FREEKASSA_SHOP_ID=<ваш Shop ID>
FREEKASSA_SECRET_WORD_1=<секретное слово 1>
FREEKASSA_SECRET_WORD_2=<секретное слово 2>
FREEKASSA_API_KEY=<API ключ>
```

**Сохраните:** `Ctrl+O`, Enter, `Ctrl+X`

---

## Шаг 8: Обновите Caddyfile

```bash
nano Caddyfile
```

**Убедитесь что указан правильный домен:**

```
{
    email admin@dudonya.online
}

dudonya.online {
    reverse_proxy backend:8000

    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer-when-downgrade"
        -Server
    }

    log {
        output file /data/access.log
        format json
    }

    tls {
        protocols tls1.2 tls1.3
    }
}
```

---

## Шаг 9: Проверка конфигов VPN

```bash
# Проверьте что конфиги на месте
ls -lh configs/

# Должно быть минимум 1 JSON файл
# У вас есть 8 файлов (Россия, США, Венгрия и т.д.)
```

---

## Шаг 10: Инициализация базы данных

```bash
cd ~/dudonya-vpn

# Создайте директории
mkdir -p data logs

# Инициализируйте БД
docker compose run --rm backend python scripts/init_db.py

# Если нужны тестовые данные:
# docker compose run --rm backend python scripts/init_db.py --test-data
```

---

## Шаг 11: Запуск всех сервисов

```bash
# Запустите в фоновом режиме
docker compose up -d

# Проверьте статус
docker compose ps

# Смотрите логи в реальном времени
docker compose logs -f

# Или отдельно по сервисам:
docker compose logs -f backend
docker compose logs -f bot
docker compose logs -f caddy
```

**Ожидаемый результат:**

```
NAME                    IMAGE                   STATUS
dudonya-backend         vpn-test3-backend       Up
dudonya-bot             vpn-test3-bot           Up
dudonya-caddy           caddy:2-alpine          Up
```

---

## Шаг 12: Проверка работы

### 12.1 Backend Health Check

```bash
# Локально
curl http://localhost:8000/health

# Или через домен (после получения SSL)
curl https://dudonya.online/health
```

**Ожидается:**
```json
{"status":"ok","timestamp":"2024-11-26T...","version":"1.0.0"}
```

### 12.2 Проверка SSL

```bash
# Подождите 1-2 минуты для получения сертификата
docker compose logs caddy | grep certificate

# Проверьте в браузере
# https://dudonya.online/health
```

### 12.3 Проверка бота

- Откройте Telegram
- Найдите вашего бота
- Отправьте `/start`
- Должно появиться меню

### 12.4 Проверка портов

```bash
# Проверьте открытые порты
netstat -tlnp | grep -E ':80|:443'

# Или
ss -tlnp | grep -E ':80|:443'
```

---

## Шаг 13: Мониторинг

```bash
# Статус контейнеров
docker compose ps

# Использование ресурсов
docker stats

# Последние логи
docker compose logs --tail=50

# Следить за логами
docker compose logs -f backend
```

---

## 🔧 Полезные команды

```bash
# Перезапуск всех сервисов
docker compose restart

# Перезапуск одного сервиса
docker compose restart backend

# Остановка
docker compose down

# Остановка с удалением volumes
docker compose down -v

# Пересборка после изменений
docker compose down
docker compose build --no-cache
docker compose up -d

# Просмотр логов конкретного сервиса
docker compose logs -f bot

# Вход в контейнер
docker compose exec backend bash
docker compose exec bot bash
```

---

## 🆘 Troubleshooting

### Проблема: DNS не обновился

**Решение:**
```bash
# Проверьте DNS
dig +short dudonya.online

# Если показывает старый IP, подождите еще
# DNS может обновляться до 30 минут

# Очистите кеш DNS локально (Windows)
# ipconfig /flushdns
```

### Проблема: Caddy не получает SSL

**Решение:**
```bash
# Проверьте логи
docker compose logs caddy

# Убедитесь что порты 80 и 443 открыты
sudo ufw status

# Проверьте что домен резолвится правильно
dig +short dudonya.online

# Перезапустите Caddy
docker compose restart caddy
```

### Проблема: Бот не отвечает

**Решение:**
```bash
# Проверьте логи
docker compose logs bot

# Проверьте BOT_TOKEN
grep BOT_TOKEN .env

# Перезапустите бота
docker compose restart bot
```

### Проблема: Backend не стартует

**Решение:**
```bash
# Проверьте логи
docker compose logs backend

# Проверьте что БД создана
ls -la data/vpn.db

# Пересоздайте БД
rm -f data/vpn.db
docker compose run --rm backend python scripts/init_db.py
docker compose up -d
```

---

## ✅ Чек-лист перед запуском

- [ ] DNS настроен (dudonya.online → 213.189.222.68)
- [ ] Docker установлен
- [ ] Firewall настроен (порты 22, 80, 443)
- [ ] Файлы проекта загружены
- [ ] .env файл заполнен (все токены)
- [ ] Caddyfile обновлен (dudonya.online)
- [ ] Конфиги VPN на месте (configs/*.json)
- [ ] База данных инициализирована
- [ ] Docker контейнеры запущены
- [ ] Backend отвечает на /health
- [ ] SSL сертификат получен
- [ ] Бот отвечает в Telegram

---

## 📞 Поддержка

После запуска сообщите результат. Если возникнут проблемы — покажите:

```bash
# Статус
docker compose ps

# Логи
docker compose logs --tail=100

# DNS
dig +short dudonya.online

# Порты
netstat -tlnp | grep -E ':80|:443'
```

---

**Успешного деплоя! 🚀**
