# 🚀 Быстрый старт — Деплой за 15 минут

**Данные сервера:**
- IP: `213.189.222.68`
- Домен: `dudonya.online`
- Бот: `@dudonyaVPN_bot`

---

## Шаг 1: Подключение и подготовка (3 мин)

```bash
# Подключитесь к серверу
ssh root@213.189.222.68

# Установите Docker и необходимое
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
apt install -y docker-compose-plugin git ufw

# Настройте firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

---

## Шаг 2: Настройка DNS (2 мин)

Добавьте A-запись в панели управления доменом:

```
Тип: A
Имя: @
Значение: 213.189.222.68
TTL: 300
```

**Проверка:**
```bash
dig +short dudonya.online
# Должно вернуть: 213.189.222.68
```

---

## Шаг 3: Клонирование и настройка (5 мин)

```bash
# Клонируйте проект
cd /opt
git clone https://github.com/WhyUcry/vpn-test3.git dudonya-vpn
cd dudonya-vpn

# Создайте .env
cp .env.example .env
nano .env
```

**Заполните .env (замените ВАШ_ТОКЕН на реальные значения):**

```env
BOT_TOKEN=ВАШ_ТОКЕН_ОТ_BOTFATHER
BOT_USERNAME=dudonyaVPN_bot
ADMIN_ID=852242429
DOMAIN=https://dudonya.online

# Платежи (хотя бы один)
CRYPTOBOT_ENABLED=true
CRYPTOBOT_TOKEN=ВАШ_ТОКЕН_CRYPTOBOT
CRYPTOBOT_ASSET=USDT

FREEKASSA_ENABLED=true
FREEKASSA_SHOP_ID=ВАШ_SHOP_ID
FREEKASSA_SECRET_WORD_1=ВАШ_SECRET_1
FREEKASSA_SECRET_WORD_2=ВАШ_SECRET_2
FREEKASSA_API_KEY=ВАШ_API_KEY
```

**Настройте домен в Caddyfile:**
```bash
nano Caddyfile
# Замените vpn.example.com на dudonya.online
# Замените admin@example.com на ваш email
```

---

## Шаг 4: Конвертация конфигов (1 мин)

```bash
# Конвертируйте ваши V2Ray конфиги в subscription-ссылки
python3 scripts/convert_configs.py

# Проверьте результат
cat configs/servers.json | head -20
```

---

## Шаг 5: Запуск (2 мин)

```bash
# Инициализируйте БД
docker compose run --rm backend python scripts/init_db.py

# Запустите все сервисы
docker compose up -d

# Проверьте статус
docker compose ps

# Смотрите логи (ждите SSL-сертификат 2-3 минуты)
docker compose logs -f
```

---

## Шаг 6: Проверка (2 мин)

```bash
# Проверка backend
curl https://dudonya.online/health
# Ожидается: {"status":"ok",...}

# Проверка бота
# Откройте Telegram → @dudonyaVPN_bot → /start
```

---

## ✅ Готово!

**Ваш VPN-сервис работает:**
- 🌐 Backend: https://dudonya.online
- 🤖 Бот: @dudonyaVPN_bot

---

## 🔧 Если что-то не работает

### Проблема: DNS не резолвится
```bash
# Подождите 5-10 минут
dig +short dudonya.online
```

### Проблема: SSL не получен
```bash
docker compose logs caddy | grep -i certificate
# Убедитесь, что DNS резолвится
# Убедитесь, что порты 80 и 443 открыты
```

### Проблема: Бот не отвечает
```bash
docker compose logs bot | tail -50
# Проверьте BOT_TOKEN в .env
docker compose restart bot
```

### Проблема: Конфиги не сконвертировались
```bash
# См. подробную инструкцию
cat CONFIGS_GUIDE.md
```

---

## 📚 Полная документация

- **Полный деплой:** [DEPLOY_FULL.md](DEPLOY_FULL.md)
- **Работа с конфигами:** [CONFIGS_GUIDE.md](CONFIGS_GUIDE.md)
- **README:** [README.md](README.md)

---

**Поддержка:** support@dudonya.online | @dudonya_support
