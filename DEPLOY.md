# 🚀 Деплой Дудоня VPN

## ✅ Что исправлено

- Автоматическая активация подписок после оплаты
- Webhook endpoints для CryptoBot и Freekassa
- Исправлены ошибки в команде `/stats`
- Добавлен GitHub Actions для автоматического деплоя
- Обновлена документация

---

## 📦 Деплой на сервер

### Шаг 1: Подготовка сервера

```bash
# Подключитесь к серверу
ssh root@YOUR_SERVER_IP

# Остановите старый проект (если есть)
cd /opt/dudonya-vpn 2>/dev/null && docker compose down
cd /opt

# Сохраните важные данные
cp dudonya-vpn/.env ~/backup_env.txt 2>/dev/null || true
cp dudonya-vpn/data/vpn.db ~/backup_db.db 2>/dev/null || true

# Удалите старую директорию
rm -rf dudonya-vpn vpn-test3

# Клонируйте проект с GitHub
git clone https://github.com/WhyUcry/vpn-test3.git dudonya-vpn
cd dudonya-vpn
```

### Шаг 2: Настройка

```bash
# Создайте .env
cp .env.example .env
nano .env
```

**Обязательно заполните:**
```env
BOT_TOKEN=1234567890:AAAA...           # От @BotFather
BOT_USERNAME=your_bot_username         # БЕЗ символа @ (например: dudonya_vpn_bot)
ADMIN_ID=123456789                     # Ваш Telegram ID
DOMAIN=https://your-domain.com         # Ваш домен

# Хотя бы один платежный провайдер:
CRYPTOBOT_TOKEN=...                    # Или
FREEKASSA_SHOP_ID=...                  # Или оба
```

**Настройте домен:**
```bash
nano Caddyfile
# Замените vpn.example.com на ваш домен
# Замените admin@example.com на ваш email
```

**Добавьте VPN-конфиги:**
```bash
nano configs/servers.json
```
Пример:
```json
{
  "configs": [
    "vless://{{UUID}}@your-server.com:443?type=tcp&security=tls#Dudonya-VPN-{{SHORT_ID}}"
  ]
}
```

### Шаг 3: Запуск

```bash
# Инициализация БД (только при первом запуске)
docker compose run --rm backend python scripts/init_db.py

# Запуск всех сервисов
docker compose up -d

# Проверка
docker compose ps
docker compose logs -f
```

### Шаг 4: Проверка

```bash
# Backend health check
curl http://localhost:8000/health

# Проверьте бота в Telegram
# Найдите бота → отправьте /start

# Проверьте домен (подождите 2-3 минуты для SSL)
curl https://your-domain.com/health
```

**Настройте webhook в Freekassa:**
- URL: `https://your-domain.com/webhook/freekassa`

✅ **Готово! Проект работает.**

---

## 🔄 Автоматический деплой (опционально)

Настройте GitHub Actions для автоматического деплоя при каждом `git push`.

### Шаг 1: SSH-ключ

```bash
# На сервере
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy

# Добавьте публичный ключ в authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

# Скопируйте приватный ключ (понадобится для GitHub)
cat ~/.ssh/github_deploy
```

### Шаг 2: GitHub Secrets

Откройте: **https://github.com/WhyUcry/vpn-test3/settings/secrets/actions**

Добавьте 5 secrets:

| Name | Value |
|------|-------|
| `SERVER_HOST` | IP вашего сервера |
| `SERVER_USER` | `root` (или `deploy`) |
| `SSH_PRIVATE_KEY` | Весь вывод `cat ~/.ssh/github_deploy` |
| `SSH_PORT` | `22` |
| `DEPLOY_PATH` | `/opt/dudonya-vpn` |

### Шаг 3: Тест

```bash
# На локальном компьютере
echo "# Test" >> README.md
git add .
git commit -m "test: auto-deploy"
git push origin main
```

Откройте **Actions** на GitHub и наблюдайте за деплоем!

✅ **Теперь каждый push автоматически деплоится на сервер.**

---

## 🔧 Полезные команды

```bash
# Просмотр логов
docker compose logs -f
docker compose logs backend
docker compose logs bot

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Обновление с GitHub
git pull origin main
docker compose down
docker compose build --no-cache
docker compose up -d

# Проверка статуса
docker compose ps
curl http://localhost:8000/health
```

---

## ⚠️ Troubleshooting

**Порт 443 занят:**
```bash
sudo systemctl stop nginx caddy apache2
docker compose up -d
```

**Docker не запускается:**
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
# Выйдите и войдите снова
```

**SSL не получен:**
```bash
# Проверьте DNS
dig +short your-domain.com

# Проверьте логи Caddy
docker compose logs caddy

# Убедитесь, что порты открыты
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

**Webhook не работает:**
```bash
# Проверьте backend логи
docker compose logs backend | grep webhook

# Проверьте доступность
curl https://your-domain.com/health

# Убедитесь, что URL настроен в Freekassa
```

**Подписка не активируется:**
```bash
# Проверьте логи бота и backend
docker compose logs bot | grep -i payment
docker compose logs backend | grep -i payment

# Проверьте, что BOT_USERNAME указан в .env
docker compose exec bot env | grep BOT_USERNAME
```

---

## 📋 Чек-лист

- [ ] Код на GitHub
- [ ] Сервер обновлен (Docker, Docker Compose)
- [ ] Старый проект остановлен
- [ ] .env настроен (включая BOT_USERNAME)
- [ ] Caddyfile обновлен с вашим доменом
- [ ] VPN-конфиги добавлены
- [ ] БД инициализирована
- [ ] Контейнеры запущены
- [ ] Backend отвечает на /health
- [ ] Бот работает в Telegram
- [ ] SSL-сертификат получен
- [ ] Webhook настроен в Freekassa

---

**Поддержка:** support@dudonya.online | @dudonya_support

**Успешного деплоя! 🎉**
