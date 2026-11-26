# Быстрая памятка по деплою на 213.189.222.68

## 🎯 Ваши данные
- **IP сервера:** 213.189.222.68
- **Hostname:** vm_00b5552a
- **Домен:** dudonya.online
- **CryptoBot токен:** 686392:AAnzKbWT4rYn6Yiy0xBVbpSyGA89wAaZWQj

---

## ⚡ Быстрый старт (5 минут)

### 1️⃣ На вашем компьютере (Windows PowerShell):

```powershell
# Перейдите в папку проекта
cd "C:\Users\admin\OneDrive\Desktop\dudonya vpn\vpn-test3"

# Загрузите проект на сервер
scp -r * root@213.189.222.68:~/dudonya-vpn/
```

### 2️⃣ На сервере (SSH):

```bash
# Подключитесь
ssh root@213.189.222.68

# Запустите автоматический деплой
cd ~/dudonya-vpn
chmod +x quick_deploy.sh
./quick_deploy.sh
```

### 3️⃣ Настройте .env:

```bash
cd ~/dudonya-vpn
nano .env
```

**Заполните минимум:**
- `BOT_TOKEN=<от @BotFather>`
- `ADMIN_ID=<ваш Telegram ID>`
- `FREEKASSA_SHOP_ID=<от freekassa.ru>`
- `FREEKASSA_SECRET_WORD_1=<от freekassa.ru>`
- `FREEKASSA_SECRET_WORD_2=<от freekassa.ru>`

**Сохраните:** Ctrl+O, Enter, Ctrl+X

### 4️⃣ Запустите:

```bash
# Инициализация БД
docker compose run --rm backend python scripts/init_db.py

# Запуск всех сервисов
docker compose up -d

# Проверка
docker compose ps
docker compose logs -f
```

### 5️⃣ Настройте DNS:

**В панели reg.ru:**
```
A запись: dudonya.online → 213.189.222.68
```

**Проверьте (подождите 5-30 минут):**
```bash
dig +short dudonya.online
# Должно вернуть: 213.189.222.68
```

---

## ✅ Проверка работы

```bash
# 1. Health check
curl http://localhost:8000/health
# Или: curl https://dudonya.online/health (после SSL)

# 2. Статус контейнеров
docker compose ps

# 3. Логи
docker compose logs backend | tail -20
docker compose logs bot | tail -20
docker compose logs caddy | tail -20

# 4. Telegram бот
# Откройте Telegram → ваш бот → /start
```

---

## 🔧 Если что-то не работает

```bash
# Перезапуск
docker compose restart

# Пересборка
docker compose down
docker compose build --no-cache
docker compose up -d

# Логи с ошибками
docker compose logs --tail=100
```

---

## 📞 Поддержка

**Документация:**
- `DEPLOY_NEW_SERVER.md` — полная инструкция
- `START_HERE.md` — общий гайд
- `FIXES.md` — известные проблемы

**Показать при проблемах:**
```bash
docker compose ps
docker compose logs --tail=50
dig +short dudonya.online
netstat -tlnp | grep ':80\|:443'
```

---

**Время деплоя: ~5-10 минут** ⚡
