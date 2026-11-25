# 🚀 Быстрый старт — Дудоня VPN

## Локальная разработка (Windows/macOS/Linux)

### 1. Установите зависимости

```bash
# Python 3.11+
python --version

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 2. Настройте конфигурацию

```bash
# Скопируйте .env.example в .env
cp .env.example .env

# Отредактируйте .env — минимум нужно:
# - BOT_TOKEN (от @BotFather)
# - ADMIN_ID (ваш Telegram ID, получите через @userinfobot)
# - Хотя бы один платежный провайдер
```

### 3. Создайте конфиг серверов

Создайте `configs/servers.json`:

```json
{
  "configs": [
    "vless://{{UUID}}@server.example.com:443?type=tcp&security=tls#Dudonya-{{SHORT_ID}}"
  ]
}
```

### 4. Инициализируйте БД

```bash
python scripts/init_db.py --test-data
```

Вы получите тестовый токен подписки.

### 5. Запустите backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend запустится на http://localhost:8000

### 6. Запустите бота (в новом терминале)

```bash
cd bot
pip install -r requirements.txt
python main.py
```

### 7. Проверьте работу

- Откройте Telegram → найдите вашего бота → `/start`
- Откройте http://localhost:8000/health (должен вернуть OK)
- Проверьте тестовую подписку: http://localhost:8000/sub/<токен>

---

## Production Deploy (Ubuntu 22.04)

### 1. Подготовка

```bash
# Установите Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Клонируйте проект
cd /opt
git clone <repo> dudonya-vpn
cd dudonya-vpn
```

### 2. Настройте DNS

Добавьте A-запись для вашего домена:

```
vpn.example.com → <IP вашего сервера>
```

### 3. Настройте .env и Caddyfile

```bash
# .env
cp .env.example .env
nano .env
# Заполните все поля

# Caddyfile
nano Caddyfile
# Замените vpn.example.com на ваш домен
```

### 4. Создайте конфиги

```bash
mkdir -p configs
nano configs/servers.json
# Добавьте ваши VPN-конфиги
```

### 5. Откройте порты

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 6. Запустите

```bash
# Инициализация БД
docker compose run --rm backend python scripts/init_db.py

# Запуск всех сервисов
docker compose up -d

# Проверка
docker compose ps
docker compose logs -f
```

### 7. Проверьте

- Откройте https://vpn.example.com/health
- Telegram → ваш бот → `/start`
- Сделайте тестовую покупку

---

## 🔧 Полезные команды

```bash
# Логи
docker compose logs -f backend
docker compose logs -f bot

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Обновление
git pull
docker compose build --no-cache
docker compose up -d

# Бэкап БД
cp data/vpn.db data/backup_$(date +%Y%m%d).db
```

---

## 📖 Подробная документация

См. **README.md** для полной инструкции, troubleshooting и production tips.

---

**Вопросы?** Проверьте раздел Troubleshooting в README.md
