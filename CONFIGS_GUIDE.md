# ⚙️ Инструкция по настройке VPN-конфигов

## 🔍 Проблема

У вас в директории `configs/` есть полные V2Ray/Xray JSON-конфиги:
- Россия.json
- Венгрия.json
- Сша.json
- Франция.json
- Хельсинки.json
- Белые списки 1-3.json

**Но:** Backend ожидает простой формат со ссылками:
```json
{
  "configs": [
    "vless://{{UUID}}@server.com:443?type=tcp&security=reality#Server-1",
    "vmess://{{UUID}}@server2.com:443?type=ws#Server-2"
  ]
}
```

## ✅ Решение 1: Автоматическая конвертация (рекомендуется)

Используйте готовый скрипт для автоматической конвертации.

### На локальном компьютере (перед деплоем):

```bash
# Перейдите в директорию проекта
cd /path/to/vpn-test3

# Запустите конвертер
python scripts/convert_configs.py
```

**Результат:**
Создастся файл `configs/servers.json` со всеми вашими серверами в правильном формате.

### На сервере (после клонирования):

```bash
cd /opt/dudonya-vpn

# Установите Python (если нет)
apt install python3 -y

# Запустите конвертер
python3 scripts/convert_configs.py

# Проверьте результат
cat configs/servers.json | head -20
```

**Что делает скрипт:**
1. Читает все .json файлы из `configs/`
2. Извлекает VLESS/VMess настройки
3. Конвертирует в subscription-ссылки
4. Заменяет фиксированные UUID на плейсхолдер `{{UUID}}`
5. Добавляет `{{SHORT_ID}}` в названия
6. Создает `configs/servers.json`

**Преимущества:**
- ✅ Каждое устройство по��учает уникальный UUID
- ✅ Работает с любым количеством серверов
- ✅ Поддерживает VLESS Reality, VMess, и другие протоколы

---

## ✅ Решение 2: Ручное создание servers.json

Если у вас есть готовые subscription-ссылки от VPN-провайдера.

### Вариант A: С плейсхолдерами (для уникальных UUID)

```bash
nano configs/servers.json
```

```json
{
  "configs": [
    "vless://{{UUID}}@ru.yourprovider.com:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=internity.ru&fp=qq&pbk=R_km5hxsfjRUsnZfSOBYxB9DwShSIwYacXduHR8_9gE&sid=dfcc5c5ac8507f95&type=tcp#Россия-{{SHORT_ID}}",
    "vless://{{UUID}}@hu.yourprovider.com:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=server.com&fp=chrome&pbk=YOUR_PUBLIC_KEY&sid=YOUR_SHORT_ID&type=tcp#Венгрия-{{SHORT_ID}}",
    "vless://{{UUID}}@us.yourprovider.com:443?type=tcp&security=tls&sni=us-server.com#США-{{SHORT_ID}}"
  ]
}
```

**Плейсхолдеры:**
- `{{UUID}}` → заменяется на уникальный UUID для каждого устройства
- `{{DEVICE_ID}}` → алиас для UUID
- `{{SHORT_ID}}` → короткий ID (8 символов) для названия

### Вариант B: Статические ссылки (одинаковые для всех устройств)

```json
{
  "configs": [
    "vless://89f55644-6d2c-4e65-8cab-ff72f2d78746@185.16.213.6:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=internity.ru&fp=qq&pbk=R_km5hxsfjRUsnZfSOBYxB9DwShSIwYacXduHR8_9gE&sid=dfcc5c5ac8507f95&type=tcp#Россия",
    "ss://base64encodedstring@server.com:8388#Shadowsocks-Server"
  ]
}
```

⚠️ **Внимание:** Некоторые VPN-провайдеры не позволяют использовать один UUID на нескольких устройствах!

---

## ✅ Решение 3: Получить ссылки от вашего VPN-провайдера

Если ваши конфиги (Россия.json, Венгрия.json и т.д.) были сгенерированы VPN-провайдером:

1. Свяжитесь с провайдером
2. Запросите **subscription-ссылки** в формате:
   - `vless://...`
   - `vmess://...`
   - `ss://...` (Shadowsocks)
   - Или subscription URL (`https://provider.com/sub/YOUR_TOKEN`)

3. Если получили subscription URL:

```bash
# Скачайте конфиги
curl https://provider.com/sub/YOUR_TOKEN | base64 -d > configs/subscription.txt

# Создайте servers.json
nano configs/servers.json
```

```json
{
  "configs": [
    "ВСТАВЬТЕ_СЮДА_ССЫЛКИ_ИЗ_SUBSCRIPTION.TXT"
  ]
}
```

---

## 🧪 Тестирование конфигов

После создания `servers.json` проверьте его:

```bash
# Проверка JSON-синтаксиса
python3 -m json.tool configs/servers.json

# Или с jq
apt install jq -y
jq . configs/servers.json
```

**Ожидаемый результат:**
```json
{
  "configs": [
    "vless://{{UUID}}@...",
    "vmess://{{UUID}}@..."
  ]
}
```

---

## 🚀 Запуск после настройки конфигов

После того как `configs/servers.json` создан:

```bash
cd /opt/dudonya-vpn

# Если backend уже запущен, перезапустите
docker compose restart backend

# Если еще не запускали
docker compose up -d

# Проверьте логи
docker compose logs backend | grep -i config

# Должно быть:
# "Loaded N config files from configs"
# "Extracted M URLs from JSON config servers.json"
```

---

## 📊 Пример: Конвертация вручную

Если скрипт не работает, конвертируйте вручную.

### Исходный конфиг (Россия.json):

```json
{
  "outbounds": [
    {
      "protocol": "vless",
      "settings": {
        "vnext": [{
          "address": "185.16.213.6",
          "port": 443,
          "users": [{
            "id": "89f55644-6d2c-4e65-8cab-ff72f2d78746",
            "encryption": "none",
            "flow": "xtls-rprx-vision"
          }]
        }]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "serverName": "internity.ru",
          "fingerprint": "qq",
          "publicKey": "R_km5hxsfjRUsnZfSOBYxB9DwShSIwYacXduHR8_9gE",
          "shortId": "dfcc5c5ac8507f95"
        }
      }
    }
  ],
  "remarks": "🇷🇺 Россия"
}
```

### Результат (subscription-ссылка):

```
vless://{{UUID}}@185.16.213.6:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=internity.ru&fp=qq&pbk=R_km5hxsfjRUsnZfSOBYxB9DwShSIwYacXduHR8_9gE&sid=dfcc5c5ac8507f95&type=tcp#🇷🇺Россия-{{SHORT_ID}}
```

**Как собрать ссылку:**

1. **Формат:** `vless://UUID@HOST:PORT?PARAMS#NAME`

2. **Параметры из конфига:**
   - `UUID` → `{{UUID}}` (плейсхолдер)
   - `HOST` → `address` (185.16.213.6)
   - `PORT` → `port` (443)
   - `encryption` → `encryption` (none)
   - `flow` → `flow` (xtls-rprx-vision)
   - `security` → `security` (reality)
   - `type` → `network` (tcp)
   
3. **Reality параметры:**
   - `sni` → `serverName`
   - `fp` → `fingerprint`
   - `pbk` → `publicKey`
   - `sid` → `shortId`

4. **Название:**
   - `#` → `remarks` + `-{{SHORT_ID}}`

---

## ❓ FAQ

### Q: Нужно ли удалять старые конфиги?

**A:** Нет, можете оставить. Backend будет загружать все файлы, но если есть `servers.json`, он будет использовать его.

**Рекомендация:** Переместите старые конфиги в подпапку:

```bash
mkdir -p configs/original
mv configs/*.json configs/original/
mv configs/original/servers.json configs/  # Вернуть servers.json
```

### Q: Сколько серверов нужно добавить?

**A:** Минимум 1, но лучше добавить столько, сколько устройств у пользователей.

**Пример:**
- Если `MAX_DEVICES=5`, добавьте минимум 5 ссылок
- Или 1 ссылку с плейсхолдером `{{UUID}}` — backend создаст 5 уникальных конфигов

### Q: Мои серверы не поддерживают уникальные UUID

**A:** Используйте статические ссылки (Решение 2, Вариант B). Но тогда все устройства одного пользователя будут иметь одинаковый UUID.

### Q: Как проверить, что конфиги работают?

**A:** После запуска backend:

```bash
# Получите тестовый токен (если создали тестовые данные)
docker compose exec backend python -c "
from backend.database import SessionLocal
from backend.models import Subscription
db = SessionLocal()
sub = db.query(Subscription).first()
if sub:
    print(f'Token: {sub.token}')
db.close()
"

# Проверьте subscription endpoint
curl https://dudonya.online/sub/ПОЛУЧЕННЫЙ_ТОКЕН

# Должны увидеть base64-закодированные конфиги
```

---

## 🎯 Итоговая рекомендация

**Для вашего случая (есть полные V2Ray конфиги):**

1. ✅ **Запустите скрипт конвертации:**
   ```bash
   python3 scripts/convert_configs.py
   ```

2. ✅ **Проверьте `configs/servers.json`:**
   ```bash
   head -20 configs/servers.json
   ```

3. ✅ **Запустите backend:**
   ```bash
   docker compose up -d
   ```

4. ✅ **Проверьте логи:**
   ```bash
   docker compose logs backend | grep config
   ```

**Если скрипт не работает:**
- Используйте **Решение 2** (ручное создание)
- Или свяжитесь с VPN-провайдером за subscription-ссылками

---

**Готово! Теперь ваши конфиги готовы к использованию.**
