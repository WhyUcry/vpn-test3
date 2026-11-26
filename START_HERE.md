# 🚀 Быстрый старт: Деплой исправленного проекта

## ✅ Что было сделано

Все ошибки исправлены! Добавлено:
- Автоматическая активация подписок после оплаты
- Webhook endpoints для CryptoBot и Freekassa
- GitHub Actions для автоматического деплоя
- Подробная документация

📖 **Полный список исправлений:** [FIXES_SUMMARY.md](FIXES_SUMMARY.md)

---

## 🎯 Что делать сейчас

Выберите один из вариантов:

### ⚡ Вариант 1: Быстро (Ручной деплой)
📖 Следуйте: [CLEANUP_AND_REDEPLOY.md](CLEANUP_AND_REDEPLOY.md)

### 🏆 Вариант 2: Правильно (Автоматический деплой)
📖 Следуйте: [DEPLOY_GITHUB.md](DEPLOY_GITHUB.md)

---

## 📝 Краткая инструкция (5 минут)

### Шаг 1: Загрузите код на GitHub

```bash
# В терминале Windows (Git Bash или PowerShell):
cd "C:\Users\admin\OneDrive\Desktop\dudonya vpn\vpn-test3"

# Проверьте статус
git status

# Добавьте все изменения
git add .

# Создайте коммит
git commit -m "fix: apply all bugfixes and add auto-deploy"

# Создайте репозиторий на GitHub:
# 1. Откройте github.com
# 2. Нажмите "New repository"
# 3. Имя: dudonya-vpn
# 4. Private (если хотите приватный)
# 5. НЕ добавляйте README, .gitignore, license
# 6. Create repository

# Добавьте remote (замените YOUR_USERNAME):
git remote add origin https://github.com/YOUR_USERNAME/dudonya-vpn.git

# Отправьте код
git branch -M main
git push -u origin main
```

✅ Код на GitHub!

### Шаг 2: Очистите сервер

```bash
# Подключитесь к серверу
ssh root@YOUR_SERVER_IP

# Найдите и остановите старый проект
cd /opt/dudonya-vpn  # или другой путь
docker compose down

# ВАЖНО: Сохраните данные!
cp .env ~/backup_env.txt
cp data/vpn.db ~/backup_db.db 2>/dev/null || true
cp -r configs ~/backup_configs 2>/dev/null || true

# Удалите старую директорию
cd /opt
rm -rf dudonya-vpn
```

✅ Сервер очищен!

### Шаг 3: Новый деплой

```bash
# Склонируйте проект с GitHub
cd /opt
git clone https://github.com/YOUR_USERNAME/dudonya-vpn.git dudonya-vpn
cd dudonya-vpn

# Настройте .env
cp .env.example .env
nano .env

# ОБЯЗАТЕЛЬНО заполните:
# - BOT_TOKEN
# - BOT_USERNAME  <-- НОВОЕ! (без @)
# - ADMIN_ID
# - DOMAIN=https://ваш-домен.com
# - CRYPTOBOT_TOKEN или FREEKASSA_* (хотя бы один)

# Настройте домен в Caddyfile
nano Caddyfile
# Замените vpn.example.com на ваш домен
# Замените admin@example.com на ваш email

# Добавьте VPN-конфиги
nano configs/servers.json

# Инициализируйте БД
docker compose run --rm backend python scripts/init_db.py

# Запустите!
docker compose up -d

# Проверьте
docker compose ps
docker compose logs -f
```

✅ Проект работает!

### Шаг 4: Проверка

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Проверьте бота в Telegram
# Найдите бота → /start

# 3. Проверьте домен (подождите 2-3 минуты для SSL)
curl https://ваш-домен.com/health

# 4. Если SSL еще не получен, смотрите логи Caddy
docker compose logs caddy
```

---

## 🎊 Готово!

Ваш проект работает с исправлениями.

### Следующие шаги:

1. **Настройте webhook в Freekassa:**
   - Зайдите в панель Freekassa
   - Укажите: `https://ваш-домен.com/webhook/freekassa`

2. **Протестируйте покупку:**
   - Откройте бота → Купить подписку
   - Выберите тариф → Оплатите
   - Подписка должна активироваться автоматически!

3. **Настройте автоматический деплой (опционально):**
   - Следуйте [DEPLOY_GITHUB.md](DEPLOY_GITHUB.md)
   - Теперь каждый push → автоматический деплой!

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| [FIXES_SUMMARY.md](FIXES_SUMMARY.md) | Полный список исправлений |
| [DEPLOY_GITHUB.md](DEPLOY_GITHUB.md) | Автоматический деплой через GitHub Actions |
| [CLEANUP_AND_REDEPLOY.md](CLEANUP_AND_REDEPLOY.md) | Очистка сервера и новый деплой |
| [README.md](README.md) | Общая документация проекта |

---

## ❓ Частые вопросы

**Q: Где взять BOT_USERNAME?**
A: Это username вашего бота БЕЗ символа @. Например: `dudonya_vpn_bot`

**Q: Нужно ли удалять старую БД?**
A: Нет! Скопируйте старую БД в новый проект. Пользователи и подписки сохранятся.

**Q: Как проверить, что платежи работают?**
A: Сделайте тестовый платеж. Проверьте логи: `docker compose logs bot | grep -i payment`

**Q: Webhook не работает**
A: 
1. Проверьте домен доступен: `curl https://домен.com/health`
2. Проверьте логи backend: `docker compose logs backend | grep webhook`
3. Проверьте URL в настройках платежной системы

---

## 🆘 Помощь

Если что-то не работает:

```bash
# 1. Проверьте логи
docker compose logs --tail=100

# 2. Проверьте конфигурацию
docker compose config

# 3. Перезапустите
docker compose restart

# 4. Полная пересборка
docker compose down
docker compose build --no-cache
docker compose up -d
```

Смотрите Troubleshooting секции в документации.

---

**Удачного деплоя! 🎉**
