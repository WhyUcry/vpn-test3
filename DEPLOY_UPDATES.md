# 🚀 Инструкция по деплою обновлений Дудоня VPN

## ✅ Что было исправлено

### 1. 🐛 Критичный баг: Оплата проходит, но подписка не выдается

**Проблема:** Backend получал webhook от платежной системы, активировал подписку, но бот не уведомлял пользователя.

**Решение:**
- Добавлена таблица `notifications` в базу данных для очереди уведомлений
- Backend создает уведомление после успешной активации подписки
- Bot имеет фоновую задачу, проверяющую новые уведомления каждые 10 секунд
- При нахождении непрочитанного уведомления бот отправляет красивое сообщение с подпиской

**Файлы изменены:**
- `backend/models.py` - добавлена модель `Notification`
- `backend/payment_processor.py` - функция `notify_user_payment_success()` теперь создает уведомление
- `bot/notification_service.py` - новый модуль для обработки уведомлений
- `bot/main.py` - запускает фоновую задачу `process_notifications()`
- `bot/keyboards.py` - добавлены новые клавиатуры

### 2. 🎨 UI/UX улучшения

**Добавлено:**
- Клавиатура после успешной оплаты с кнопками "Моя подписка", "Как подключить", "Главное меню"
- Клавиатура для отмены оплаты (готова к использованию в handlers)
- Красивое форматирование сообщений с эмодзи

### 3. 🌐 Лендинг на dudonya.online

**Создан:**
- Одностраничный сайт с информацией о VPN
- Анимация рыжего лисенка (выглядывает и виляет хвостом)
- Теплые цвета (кремовый, персиковый, оранжевый, рыжий)
- Кнопки в стиле iOS с blur-эффектами
- Адаптивный дизайн (mobile-first)
- Преимущества, тарифы, инструкция "Как это работает"
- Прямая кнопка к Telegram-боту

**Настройка:**
- Caddy раздает статику на корневом домене
- API endpoints (/sub/*, /webhook/*, /health) остаются на том же домене

---

## 🔧 Деплой на сервер

### Шаг 1: Подготовка (на локальной машине)

```bash
# Закоммитьте изменения
git add .
git commit -m "fix: payment notifications, landing page, and UI improvements"
git push origin main
```

### Шаг 2: Обновление на сервере

```bash
# Подключитесь к серверу
ssh root@213.189.222.68

# Перейдите в директорию проекта
cd ~/dudonya-vpn

# Остановите контейнеры
docker compose down

# Получите последние изменения
git pull origin main

# Запустите миграцию для добавления таблицы notifications
docker compose run --rm backend python scripts/migrate_add_notifications.py
```

**Ожидаемый вывод:**
```
Creating notifications table...
✅ Notifications table created successfully
```

### Шаг 3: Пересборка и запуск

```bash
# Пересоберите образы (важно для обновления кода бота)
docker compose build --no-cache bot backend

# Запустите все сервисы
docker compose up -d

# Проверьте статус
docker compose ps
```

**Ожидаемый результат:**
```
NAME              STATUS
dudonya-backend   Up (healthy)
dudonya-bot       Up
dudonya-caddy     Up
```

### Шаг 4: Проверка логов

```bash
# Смотрите логи всех сервисов
docker compose logs -f
```

**Что искать в логах:**

✅ **Backend:**
```
Backend started successfully
```

✅ **Bot:**
```
Bot started, polling for updates...
Notification service started
```

✅ **Caddy:**
```
certificate obtained successfully
```

**Нажмите `Ctrl+C` для выхода из логов**

### Шаг 5: Тестирование

#### 5.1. Проверка лендинга

Откройте в браузере:
```
https://dudonya.online
```

Должен открыться красивый лендинг с анимацией лисенка 🦊

#### 5.2. Проверка API

```bash
curl https://dudonya.online/health
```

**Ожидается:**
```json
{"status":"ok","timestamp":"...","version":"1.0.0"}
```

#### 5.3. Проверка бота

1. Откройте Telegram
2. Найдите: `@dudonyaVPN_bot`
3. Отправьте: `/start`
4. Бот должен ответить с меню

#### 5.4. Тестовая оплата (ВАЖНО!)

**Это самый важный тест для проверки исправления бага:**

1. В боте нажмите "💰 Купить подписку"
2. Выберите тариф (например, 1 месяц)
3. Выберите способ оплаты (CryptoBot или Freekassa)
4. Оплатите (можно минимальную тестовую сумму)
5. **ОЖИДАЕМОЕ ПОВЕДЕНИЕ:**
   - После оплаты вы должны получить сообщение от бота:
   ```
   ✅ Оплата успешно получена!
   
   💎 Ваша подписка активирована на 30 дней
   📅 Действует до: ДД.ММ.ГГГГ
   📱 Устройств: 1
   
   🔗 Ссылка для подключения:
   https://dudonya.online/sub/XXXXXXXXX
   
   👇 Нажмите кнопку ниже...
   ```
   - Должны быть кнопки: "📱 Моя подписка", "📖 Как подключить", "🏠 Главное меню"

6. **Если сообщение НЕ ПРИШЛО:**
   ```bash
   # Проверьте логи бота
   docker compose logs bot | tail -50
   
   # Проверьте таблицу notifications
   docker compose exec backend python -c "
   from backend.db import SessionLocal
   from backend.models import Notification
   db = SessionLocal()
   notifs = db.query(Notification).all()
   for n in notifs:
       print(f'ID: {n.id}, User: {n.telegram_id}, Type: {n.type}, Sent: {n.sent}')
   db.close()
   "
   ```

---

## 🔍 Мониторинг уведомлений

Проверить работу системы уведомлений:

```bash
# Смотрите логи бота в реальном времени
docker compose logs -f bot

# Ищите строки:
# "Found N pending notifications"  - найдены непрочитанные уведомления
# "Sent payment success notification to TELEGRAM_ID" - уведомление отправлено
```

---

## ⚙️ Конфигурация

### Настройка интервала проверки уведомлений

По умолчанию бот проверяет уведомления каждые **10 секунд**.

Чтобы изменить:

```python
# В bot/main.py, строка с process_notifications
notification_task = asyncio.create_task(
    process_notifications(bot, check_interval=10)  # <-- измените здесь
)
```

Рекомендуемые значения:
- **5-10 секунд** - для продакшена (быстрое уведомление пользователей)
- **30-60 секунд** - если хотите снизить нагрузку на БД

---

## 📊 База данных

### Таблица notifications

**Структура:**
- `id` - ID уведомления
- `user_id` - ID пользователя в таблице users
- `telegram_id` - Telegram ID пользователя
- `type` - Тип уведомления (payment_success, subscription_extended, device_added)
- `subscription_id` - ID подписки (если применимо)
- `payment_id` - ID платежа (если применимо)
- `data` - JSON с дополнительными данными
- `sent` - Статус (0 = pending, 1 = sent, 2 = failed)
- `created_at` - Дата создания
- `sent_at` - Дата отправки

### Просмотр уведомлений

```bash
# Войдите в контейнер backend
docker compose exec backend sh

# Откройте Python shell
python

# Выполните:
from backend.db import SessionLocal
from backend.models import Notification
db = SessionLocal()

# Все уведомления
notifications = db.query(Notification).all()
for n in notifications:
    print(f"{n.id}: User {n.telegram_id}, Type: {n.type.value}, Sent: {n.sent}")

# Только непрочитанные
pending = db.query(Notification).filter(Notification.sent == 0).all()
print(f"Pending: {len(pending)}")

db.close()
exit()
```

---

## 🐛 Troubleshooting

### Проблема: Уведомления не отправляются

**Решение 1: Проверьте фоновую задачу**
```bash
docker compose logs bot | grep "Notification service"
# Должно быть: "Notification service started"
```

**Решение 2: Проверьте наличие непрочитанных уведомлений**
```bash
docker compose exec backend python -c "
from backend.db import SessionLocal
from backend.models import Notification
db = SessionLocal()
count = db.query(Notification).filter(Notification.sent == 0).count()
print(f'Pending notifications: {count}')
db.close()
"
```

**Решение 3: Перезапустите бота**
```bash
docker compose restart bot
docker compose logs -f bot
```

### Проблема: Лендинг не открывается

**Решение 1: Проверьте директорию landing**
```bash
ls -la ~/dudonya-vpn/landing/
# Должен быть файл index.html
```

**Решение 2: Проверьте Caddy**
```bash
docker compose logs caddy | grep -i error
docker compose restart caddy
```

**Решение 3: Проверьте права доступа**
```bash
chmod 755 ~/dudonya-vpn/landing
chmod 644 ~/dudonya-vpn/landing/index.html
```

### Проблема: Оплата проходит, но уведомление не создается

**Решение 1: Проверьте логи backend**
```bash
docker compose logs backend | grep -i "payment"
docker compose logs backend | grep -i "notification"
```

**Решение 2: Проверьте вебхук**
```bash
# Проверьте, что вебхук приходит в backend
docker compose logs backend | grep -i "webhook"
```

**Решение 3: Проверьте функцию process_successful_payment**
```bash
docker compose logs backend | grep -i "Processing payment"
```

---

## 📋 Чек-лист после деплоя

- [ ] Контейнеры запущены и работают
- [ ] Backend отвечает на `/health`
- [ ] Лендинг открывается на `https://dudonya.online`
- [ ] Бот отвечает на `/start`
- [ ] Фоновая задача уведомлений запущена (в логах бота)
- [ ] Таблица `notifications` создана в БД
- [ ] Тестовая оплата прошла успешно
- [ ] После оплаты получено уведомление от бота с подпиской
- [ ] Ссылка подписки работает (можно проверить через curl)
- [ ] Инструкции в боте работают
- [ ] Кнопки "Моя подписка", "Как подключить" работают

---

## 🎯 Следующие шаги (опционально)

### 1. Добавить кнопку "Отменить оплату"

В `bot/handlers.py` найдите функцию обработки выбора способа оплаты и добавьте:

```python
await message.answer(
    text,
    reply_markup=keyboards.get_cancel_payment_keyboard("main_menu")
)
```

### 2. Добавить обработку возврата с платежной страницы

В `bot/handlers.py` добавьте обработчик deep links:

```python
@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    # ... existing code ...
    
    # Check for payment result
    if command.args:
        if command.args.startswith("paid_"):
            order_id = command.args[5:]
            await handle_payment_success(message, order_id)
            return
        elif command.args == "fail":
            await message.answer(
                "❌ Оплата отменена или не прошла. Вы можете попробовать снова.",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
            return
```

### 3. Мониторинг через Uptime Kuma

См. инструкцию в `DEPLOY_FULL.md`

---

## 🆘 Поддержка

Если возникли проблемы:

1. Проверьте логи: `docker compose logs -f`
2. Проверьте статус: `docker compose ps`
3. Перезапустите: `docker compose restart`

**Контакты:**
- Telegram: @dudonya_support
- Email: support@dudonya.online

---

**🎉 Поздравляем! Дудоня VPN обновлен и готов к продакшену!**
