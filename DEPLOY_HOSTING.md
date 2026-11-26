# Деплой на server261.hosting.reg.ru под доменом dudonya.online

## 📋 Информация о хостинге

- **Хостинг**: server261.hosting.reg.ru
- **Панель**: https://server261.hosting.reg.ru:1500/
- **Домен**: dudonya.online
- **SSL**: Автоматический через Caddy (Let's Encrypt)

---

## 🚀 Пошаговая инструкция по деплою

### Шаг 1: Подключение к серверу по SSH

```bash
# Получите SSH доступ в панели управления хостингом
ssh your_username@server261.hosting.reg.ru

# Или через конкретный IP
ssh your_username@<IP адрес>
```

### Шаг 2: Проверка установленного ПО

```bash
# Проверьте Docker
docker --version
docker compose version

# Если Docker не установлен
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### Шаг 3: Загрузка проекта на сервер

**Вариант А: Через Git**
```bash
cd ~
git clone <your-repo-url> dudonya-vpn
cd dudonya-vpn
```

**Вариант Б: Через SFTP/SCP**
```bash
# На вашем локальном компьютере
scp -r /c/Users/admin/OneDrive/Desktop/dudonya\ vpn/vpn-test3/* your_username@server261.hosting.reg.ru:~/dudonya-vpn/
```

### Шаг 4: Настройка DNS для dudonya.online

1. Войдите в панель управления доменом (reg.ru)
2. Перейдите в настройки DNS для dudonya.online
3. Добавьте/обновите A-запись:

```
Тип    Имя                 Значение
A      @                   <IP сервера server261>
A      vpn                 <IP сервера server261>
```

4. Дождитесь обновления DNS (5-30 минут):
```bash
# Проверьте DNS
dig +short dudonya.online
dig +short vpn.dudonya.online
```

### Шаг 5: Создайте .env файл

```bash
cd ~/dudonya-vpn
nano .env
```

**Вставьте следующее содержимое:**

```env
# Telegram Bot
BOT_TOKEN=<ваш токен от @BotFather>
ADMIN_ID=<ваш Telegram ID>

# Domain
DOMAIN=https://dudonya.online

# Database
DATABASE_URL=sqlite:///data/vpn.db
CONFIGS_DIR=/app/configs

# Pricing (установите реальные цены)
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
CRYPTOBOT_TOKEN=<ваш CryptoBot token>
CRYPTOBOT_ASSET=USDT

# Freekassa (Фрикасса)
FREEKASSA_ENABLED=true
FREEKASSA_SHOP_ID=<ваш Shop ID>
FREEKASSA_SECRET_WORD_1=<первое секретное слово>
FREEKASSA_SECRET_WORD_2=<второе секретное слово>
FREEKASSA_API_KEY=<API ключ>
```

**Сохраните**: `Ctrl+O`, Enter, `Ctrl+X`

### Шаг 6: Обновите Caddyfile

```bash
nano Caddyfile
```

Замените `vpn.example.com` на `dudonya.online`:

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

### Шаг 7: Создайте конфиг серверов

```bash
nano configs/servers.json
```

**Добавьте ваши VPN-конфиги:**

```json
{
  "configs": [
    "vless://{{UUID}}@your-server.com:443?type=tcp&security=tls&sni=your-server.com#Dudonya-{{SHORT_ID}}"
  ]
}
```

### Шаг 8: Настройте firewall (если есть)

```bash
# Проверьте firewall
sudo ufw status

# Если активен, откройте порты
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Шаг 9: Инициализируйте базу данных

```bash
# Создайте директории
mkdir -p data logs

# Инициализируйте БД
docker compose run --rm backend python scripts/init_db.py

# Или с тестовыми данными
docker compose run --rm backend python scripts/init_db.py --test-data
```

### Шаг 10: Запустите сервисы

```bash
# Запустите все контейнеры
docker compose up -d

# Проверьте статус
docker compose ps

# Должно быть:
# dudonya-backend   running
# dudonya-bot       running
# dudonya-caddy     running
```

### Шаг 11: Проверьте логи

```bash
# Все логи
docker compose logs -f

# Backend
docker compose logs -f backend

# Bot
docker compose logs -f bot

# Caddy (SSL)
docker compose logs -f caddy
```

**Ожидаемые логи:**
- Backend: "Starting Dudonya VPN Backend..."
- Bot: "Bot started, polling for updates..."
- Caddy: "certificate obtained successfully" (после получения SSL)

### Шаг 12: Проверка работы

#### 1. Проверьте backend
```bash
curl https://dudonya.online/health

# Ожидается:
# {"status":"ok","timestamp":"...","version":"1.0.0"}
```

#### 2. Проверьте бота
- Откройте Telegram
- Найдите вашего бота
- Отправьте `/start`
- Должно появиться меню

#### 3. Проверьте SSL
```bash
curl -I https://dudonya.online
# Должен вернуть 200 OK
```

Откройте в браузере: `https://dudonya.online/health`

---

## 🔧 Управление сервисом

### Перезапуск
```bash
docker compose restart

# Или отдельный сервис
docker compose restart backend
docker compose restart bot
```

### Остановка
```bash
docker compose down
```

### Обновление кода
```bash
# Получите изменения
git pull

# Пересоберите
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Просмотр логов
```bash
# Real-time логи
docker compose logs -f

# Последние 100 строк
docker compose logs --tail=100

# Логи на диске
tail -f logs/backend_*.log
tail -f logs/bot_*.log
```

### Бэкап базы данных
```bash
# Ручной бэкап
cp data/vpn.db data/vpn_backup_$(date +%Y%m%d).db

# Автоматический бэкап (cron)
crontab -e
# Добавьте:
0 3 * * * cp ~/dudonya-vpn/data/vpn.db ~/dudonya-vpn/data/backup_$(date +\%Y\%m\%d).db
```

---

## ⚠️ Troubleshooting

### Проблема: SSL не получается

**Решение:**
```bash
# 1. Проверьте DNS
dig +short dudonya.online
# Должен вернуть IP сервера

# 2. Проверьте порты
sudo netstat -tlnp | grep ':80\|:443'

# 3. Проверьте логи Caddy
docker compose logs caddy

# 4. Перезапустите Caddy
docker compose restart caddy
```

### Проблема: Бот не отвечает

**Решение:**
```bash
# Проверьте статус
docker compose ps

# Проверьте логи
docker compose logs bot

# Убедитесь что BOT_TOKEN правильный
grep BOT_TOKEN .env
```

### Проблема: Backend недоступен

**Решение:**
```bash
# Проверьте health
docker compose exec backend curl http://localhost:8000/health

# Проверьте логи
docker compose logs backend

# Проверьте конфиги
ls -la configs/
```

---

## 📊 Мониторинг

### Простой мониторинг
```bash
# Health check каждые 5 минут
watch -n 300 'curl -s https://dudonya.online/health'
```

### Использование ресурсов
```bash
# CPU и память
docker stats

# Место на диске
df -h
du -sh ~/dudonya-vpn/data
```

---

## 🔒 Безопасность

1. **Не коммитьте .env** в Git
2. **Регулярно делайте бэкапы** базы данных
3. **Мониторьте логи** на ошибки
4. **Обновляйте Docker** образы регулярно

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker compose logs -f`
2. Проверьте DNS: `dig +short dudonya.online`
3. Проверьте firewall: `sudo ufw status`
4. Обратитесь в поддержку хостинга: https://www.reg.ru/support/

---

**Готово! Ваш VPN-сервис работает на https://dudonya.online** 🚀
