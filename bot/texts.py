"""Text messages and instructions for Dudonya VPN bot."""

# Welcome message
WELCOME_TEXT = """
👋 Добро пожаловать в <b>Дудоня VPN</b>!

Быстрый и надёжный VPN для обхода блокировок.

🌐 Работает в Happ, v2rayNG, Streisand, Hiddify, Shadowrocket
📱 До 5 устройств на один аккаунт
⚡ Мгновенное подключение после оплаты

Выберите действие:
"""

# Subscription info
SUBSCRIPTION_INFO_TEMPLATE = """
📱 <b>Ваша подписка</b>

🔐 Токен: <code>{token}</code>

📊 Статус: {status}
📅 Действительна до: <b>{expires_at}</b>
📱 Устройства: <b>{devices_current} из {devices_max}</b>

🔗 Ссылка подписки:
<code>{url}</code>

💡 <i>Скопируйте ссылку и добавьте её в ваше VPN-приложение</i>
"""

SUBSCRIPTION_ACTIVE = "✅ Активна"
SUBSCRIPTION_EXPIRED = "❌ Истекла"

NO_SUBSCRIPTION_TEXT = """
❌ У вас пока нет активной подписки.

Выберите тариф и оплатите, чтобы начать пользоваться VPN.
"""

# Pricing
PRICING_TEXT = """
💰 <b>Выберите тариф</b>

📅 <b>1 месяц</b> — {price_1m} {currency}
📅 <b>3 месяца</b> — {price_3m} {currency} <i>(выгода {discount_3m}%)</i>
📅 <b>12 месяцев</b> — {price_12m} {currency} <i>(выгода {discount_12m}%)</i>

🎁 Базовый тариф: <b>{base_devices} устройство</b>
➕ Дополнительные устройства: <b>{price_per_device} {currency}</b> за слот (до {max_devices} устройств)
"""

# Extra device
EXTRA_DEVICE_INFO = """
📱 <b>Докупить устройство</b>

Текущий лимит: <b>{current} из {max}</b> устройств

Цена дополнительного слота: <b>{price} {currency}</b>

После оплаты вы сможете использовать подписку ещё на одном устройстве.

💡 <i>Просто обновите подписку в приложении — новый слот появится автоматически</i>
"""

EXTRA_DEVICE_LIMIT_REACHED = """
⚠️ Вы уже используете максимальное количество устройств (<b>{max}</b>).

Докупить больше слотов невозможно.
"""

EXTRA_DEVICE_NO_SUBSCRIPTION = """
❌ У вас нет активной подписки.

Сначала купите подписку, затем сможете докупить дополнительные устройства.
"""

# Payment
PAYMENT_METHOD_TEXT = """
💳 <b>Выберите способ оплаты</b>

Тариф: <b>{plan}</b>
Сумма: <b>{amount} {currency}</b>
"""

PAYMENT_CREATED = """
✅ Счёт создан!

Сумма: <b>{amount} {currency}</b>
Провайдер: <b>{provider}</b>

Перейдите по ссылке для оплаты:
{url}

⏱ Счёт действителен 15 минут
"""

PAYMENT_SUCCESS = """
✅ <b>Оплата успешно получена!</b>

Ваша подписка активирована до: <b>{expires_at}</b>
Устройств: <b>{devices}</b>

🔗 Ссылка подписки:
<code>{url}</code>

📲 Нажмите «Как подключить» для инструкции
"""

PAYMENT_FAILED = """
❌ <b>Ошибка оплаты</b>

{reason}

Попробуйте ещё раз или выберите другой способ оплаты.
"""

# Instructions
INSTRUCTIONS_MENU = """
📖 <b>Инструкции по подключению</b>

Выберите ваше приложение:
"""

INSTRUCTIONS_HAPP = """
📱 <b>Happ VPN</b>

1️⃣ Установите Happ:
   • iOS: App Store
   • Android: Google Play или happ.su
   • Другое: happ.su/download

2️⃣ Откройте приложение → нажмите <b>«+»</b>

3️⃣ Выберите <b>«Импорт подписки»</b> или <b>«Добавить из буфера»</b>

4️⃣ Вставьте вашу ссылку подписки

5️⃣ В списке появится <b>«Дудоня VPN»</b> с несколькими серверами (по числу устройств)

6️⃣ Выберите любой сервер → нажмите <b>«Подключить»</b>

✅ Готово! VPN работает.

💡 Подписка обновляется автоматически каждые 12 часов
"""

INSTRUCTIONS_V2RAYNG = """
📱 <b>v2rayNG (Android)</b>

1️⃣ Установите v2rayNG из Google Play или GitHub

2️⃣ Откройте меню (☰) → <b>«Группы»</b>

3️⃣ Нажмите <b>«+»</b> → <b>«Импорт из буфера обмена»</b>

4️⃣ Вставьте вашу ссылку → нажмите <b>«Сохранить»</b>

5️⃣ Обновите группу (нажмите ⟳)

6️⃣ Выберите сервер из списка → нажмите <b>▶</b>

✅ Готово!
"""

INSTRUCTIONS_STREISAND = """
📱 <b>Streisand (iOS/macOS)</b>

1️⃣ Установите Streisand из App Store

2️⃣ Нажмите <b>«+»</b> → <b>«Добавить подписку»</b>

3️⃣ Вставьте URL вашей подписки → <b>«Добавить»</b>

4️⃣ Выберите сервер → подключитесь

✅ Готово!
"""

INSTRUCTIONS_HIDDIFY = """
📱 <b>Hiddify</b>

1️⃣ Установите Hiddify (iOS, Android, Windows, macOS)

2️⃣ Нажмите <b>«+»</b> → <b>«Добавить по ссылке»</b>

3️⃣ Вставьте вашу ссылку подписки → <b>«Сохранить»</b>

4️⃣ Выберите сервер → подключитесь

✅ Готово!
"""

INSTRUCTIONS_SHADOWROCKET = """
📱 <b>Shadowrocket (iOS)</b>

1️⃣ Купите и установите Shadowrocket из App Store ($2.99)

2️⃣ Нажмите <b>«+»</b> → <b>«Subscribe»</b>

3️⃣ В поле URL вставьте вашу ссылку → <b>«Save»</b>

4️⃣ Обновите подписку (свайпом вниз)

5️⃣ Выберите сервер → подключитесь

✅ Готово!
"""

# Support
SUPPORT_TEXT = """
💬 <b>Поддержка</b>

Возникли вопросы или проблемы?

📧 Email: support@dudonya-vpn.com
💬 Telegram: @dudonya_support

Мы ответим в течение 24 часов.
"""

# Admin
STATS_TEMPLATE = """
📊 <b>Статистика</b>

👥 Пользователей: <b>{total_users}</b>
📱 Активных подписок: <b>{active_subscriptions}</b>
💰 Выручка за всё время:

💳 CryptoBot: <b>{revenue_cryptobot} USDT</b>
💳 ЮKassa: <b>{revenue_yookassa} RUB</b>
💳 Робокасса: <b>{revenue_robokassa} RUB</b>

📅 Дата: <b>{date}</b>
"""

GRANT_SUCCESS = """
✅ Подписка выдана пользователю <code>{telegram_id}</code>

Срок: <b>{days} дней</b>
Устройств: <b>{devices}</b>
"""

REVOKE_SUCCESS = """
✅ Подписка пользователя <code>{telegram_id}</code> отозвана.
"""

BROADCAST_CONFIRM = """
📢 <b>Рассылка</b>

Сообщение:
{text}

Отправить всем пользователям?
"""

BROADCAST_STARTED = """
📢 Рассылка началась...

Пользователей: <b>{total}</b>
"""

BROADCAST_COMPLETED = """
✅ <b>Рассылка завершена</b>

Отправлено: <b>{sent}</b>
Ошибок: <b>{failed}</b>
"""

# Errors
ERROR_GENERIC = """
❌ Произошла ошибка. Попробуйте ещё раз или обратитесь в поддержку.
"""

ERROR_PAYMENT_PROVIDER_DISABLED = """
⚠️ Этот способ оплаты временно недоступен. Выберите другой.
"""
