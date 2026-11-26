# Очистка сервера и новый деплой

Эта инструкция поможет вам:
1. Удалить старый проект с сервера
2. Очистить Docker контейнеры и образы
3. Заново задеплоить проект через GitHub

---

## 🧹 Шаг 1: Подключитесь к серверу

```bash
ssh root@YOUR_SERVER_IP
# или
ssh deploy@YOUR_SERVER_IP
```

---

## 🛑 Шаг 2: Остановите и удалите старые контейнеры

### 2.1. Найдите директорию со старым проектом

```bash
# Обычно проект находится в:
cd /opt/dudonya-vpn
# или
cd /root/dudonya-vpn
# или
cd ~/dudonya-vpn

# Если не помните, найдите:
find / -name "docker-compose.yml" -path "*/dudonya-vpn/*" 2>/dev/null
```

### 2.2. Остановите контейнеры

```bash
cd /path/to/old/project
docker compose down

# Или если проект назывался иначе:
docker compose -p dudonya down
docker compose -p vpn-test3 down

# Проверьте все запущенные контейнеры
docker ps -a
```

### 2.3. Остановите контейнеры вручную (если нужно)

```bash
# Список всех контейнеров
docker ps -a

# Остановите контейнеры по имени
docker stop dudonya-backend dudonya-bot dudonya-caddy
docker rm dudonya-backend dudonya-bot dudonya-caddy

# Или остановите все контейнеры
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```

---

## 🗑️ Шаг 3: Удалите старый проект

### 3.1. Сохраните важные файлы (если нужно)

```bash
# Создайте резервную копию .env
cp /path/to/old/project/.env ~/backup_env_$(date +%Y%m%d).txt

# Создайте резервную копию базы данных
cp /path/to/old/project/data/vpn.db ~/backup_db_$(date +%Y%m%d).db

# Сохраните конфиги
cp -r /path/to/old/project/configs ~/backup_configs_$(date +%Y%m%d)
```

### 3.2. Удалите директорию проекта

```bash
# ВАЖНО: Убедитесь, что вы в правильной директории!
cd /path/to/old/project
pwd  # Проверьте путь

# Удалите проект
cd ..
sudo rm -rf dudonya-vpn

# Или если нужно удалить с другим именем:
sudo rm -rf vpn-test3
```

---

## 🧼 Шаг 4: Очистите Docker (опционально)

### 4.1. Удалите неиспользуемые образы

```bash
# Удалить все остановленные контейнеры
docker container prune -f

# Удалить все неиспользуемые образы
docker image prune -a -f

# Удалить все неиспользуемые volumes
docker volume prune -f

# Удалить все неиспользуемые сети
docker network prune -f

# Полная очистка (осторожно!)
docker system prune -a --volumes -f
```

### 4.2. Проверьте освободившееся место

```bash
df -h
docker system df
```

---

## 📦 Шаг 5: Подготовьте GitHub репозиторий

### 5.1. На локальном компьютере

```bash
# Перейдите в директорию проекта
cd /path/to/local/dudonya-vpn

# Убедитесь, что все изменения закоммичены
git status

# Добавьте все файлы
git add .

# Создайте коммит
git commit -m "fix: apply all bugfixes and add GitHub Actions deployment"

# Создайте репозиторий на GitHub (если еще не создан)
# Перейдите на github.com > New repository > dudonya-vpn

# Добавьте remote
git remote add origin https://github.com/YOUR_USERNAME/dudonya-vpn.git

# Отправьте код на GitHub
git branch -M main
git push -u origin main
```

### 5.2. Проверьте, что .gitignore настроен

Убедитесь, что файл `.gitignore` содержит:

```gitignore
# Environment
.env
.env.local

# Data
data/
*.db
*.sqlite

# Logs
logs/
*.log

# Docker
docker-compose.override.yml

# IDE
.vscode/
.idea/
*.swp
*.swo

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
```

**ВАЖНО:** Не коммитьте `.env` файл с реальными токенами!

---

## 🚀 Шаг 6: Новый деплой через GitHub

### Вариант A: Автоматический деплой (рекомендуется)

Следуйте подробной инструкции: **[DEPLOY_GITHUB.md](DEPLOY_GITHUB.md)**

Краткая версия:

1. **На сервере:**
   ```bash
   # Создайте директорию
   cd /opt
   sudo mkdir -p dudonya-vpn
   sudo chown $USER:$USER dudonya-vpn
   
   # Клонируйте репозиторий
   git clone https://github.com/YOUR_USERNAME/dudonya-vpn.git dudonya-vpn
   cd dudonya-vpn
   
   # Настройте .env
   cp .env.example .env
   nano .env  # Заполните токены
   
   # Настройте Caddyfile
   nano Caddyfile  # Укажите ваш домен
   
   # Добавьте VPN-конфиги
   nano configs/servers.json
   
   # Инициализируйте БД
   docker compose run --rm backend python scripts/init_db.py
   
   # Запустите
   docker compose up -d
   ```

2. **Настройте GitHub Actions:**
   - Добавьте GitHub Secrets (см. DEPLOY_GITHUB.md)
   - Теперь каждый push автоматически деплоится!

### Вариант B: Ручной деплой

```bash
# На сервере
cd /opt
git clone https://github.com/YOUR_USERNAME/dudonya-vpn.git dudonya-vpn
cd dudonya-vpn

# Настройте .env
cp .env.example .env
nano .env

# Настройте Caddyfile
nano Caddyfile

# Добавьте конфиги
mkdir -p configs
nano configs/servers.json

# Инициализируйте БД
docker compose run --rm backend python scripts/init_db.py

# Запустите
docker compose up -d

# Проверьте
docker compose ps
docker compose logs -f
curl http://localhost:8000/health
```

---

## ✅ Шаг 7: Проверка работы

### 7.1. Проверьте контейнеры

```bash
docker compose ps
```

Ожидаемый вывод:
```
NAME                IMAGE                    STATUS
dudonya-backend     dudonya-vpn-backend      Up (healthy)
dudonya-bot         dudonya-vpn-bot          Up
dudonya-caddy       caddy:2-alpine           Up
```

### 7.2. Проверьте backend

```bash
# Локально
curl http://localhost:8000/health

# Через домен
curl https://your-domain.com/health
```

Ожидается:
```json
{"status":"ok","timestamp":"2024-01-01T12:00:00","version":"1.0.0"}
```

### 7.3. Проверьте бота

Откройте Telegram → найдите вашего бота → отправьте `/start`

### 7.4. Проверьте SSL

```bash
curl -I https://your-domain.com
```

Должен вернуть статус `200 OK` с HTTPS.

### 7.5. Проверьте логи

```bash
# Все логи
docker compose logs --tail=50

# Backend
docker compose logs -f backend

# Bot
docker compose logs -f bot

# Ошибки
docker compose logs | grep -i error
```

---

## 🔧 Восстановление данных (если нужно)

Если вы сохранили резервные копии:

### Восстановить базу данных

```bash
# Остановите контейнеры
docker compose down

# Скопируйте старую БД
cp ~/backup_db_YYYYMMDD.db ./data/vpn.db

# Запустите контейнеры
docker compose up -d
```

### Восстановить конфиги

```bash
# Скопируйте старые конфиги
cp -r ~/backup_configs_YYYYMMDD/* ./configs/

# Перезапустите backend
docker compose restart backend
```

---

## ⚠️ Проблемы и решения

### Порты уже заняты

**Ошибка:**
```
Error: Bind for 0.0.0.0:443 failed: port is already allocated
```

**Решение:**
```bash
# Найдите процесс
sudo lsof -i :443
sudo lsof -i :80

# Остановите старый Caddy/Nginx
sudo systemctl stop caddy
sudo systemctl stop nginx

# Или убейте процесс
sudo kill -9 <PID>
```

### Docker daemon not running

**Решение:**
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Permission denied

**Решение:**
```bash
# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Выйдите и войдите снова
exit
# Затем подключитесь заново
```

### Git clone failed (приватный репозиторий)

**Решение:**

1. **Через HTTPS с токеном:**
   ```bash
   git clone https://USERNAME:TOKEN@github.com/USERNAME/dudonya-vpn.git
   ```

2. **Через SSH:**
   ```bash
   # Создайте SSH-ключ
   ssh-keygen -t ed25519 -C "server@dudonya-vpn"
   
   # Скопируйте публичный ключ
   cat ~/.ssh/id_ed25519.pub
   
   # Добавьте в GitHub Settings > SSH Keys
   
   # Клонируйте
   git clone git@github.com:USERNAME/dudonya-vpn.git
   ```

---

## 📋 Чек-лист

- [ ] Старые контейнеры остановлены и удалены
- [ ] Старая директория проекта удалена
- [ ] Docker очищен от неиспользуемых образов
- [ ] Код залит на GitHub (без .env!)
- [ ] Репозиторий склонирован на сервер
- [ ] .env файл настроен
- [ ] Caddyfile обновлен
- [ ] VPN-конфиги добавлены
- [ ] База данных инициализирована
- [ ] Контейнеры запущены
- [ ] Backend отвечает на /health
- [ ] Бот работает в Telegram
- [ ] SSL-сертификат получен
- [ ] GitHub Actions настроен (опционально)

---

## 🎉 Готово!

Теперь у вас:
- ✅ Чистый сервер
- ✅ Свежий деплой проекта
- ✅ Автоматический деплой через GitHub (опционально)
- ✅ Все баги исправлены

**Следующие шаги:**

1. Настройте webhook'и в CryptoBot и Freekassa
2. Протестируйте покупку подписки
3. Настройте мониторинг
4. Настройте автоматические бэкапы

**Поддержка:**

- 📧 Email: support@dudonya.online
- 💬 Telegram: @dudonya_support

---

**Успешного деплоя! 🚀**
