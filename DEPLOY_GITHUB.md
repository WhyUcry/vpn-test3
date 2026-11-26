# Автоматический деплой через GitHub Actions

Эта инструкция описывает, как настроить автоматический деплой проекта Дудоня VPN на ваш сервер через GitHub Actions.

## 🎯 Что будет настроено

После настройки каждый push в ветку `main` будет автоматически:
1. Подключаться к вашему серверу по SSH
2. Скачивать последние изменения из GitHub
3. Пересобирать Docker-контейнеры
4. Перезапускать все сервисы
5. Проверять работоспособность

## 📋 Требования

- ✅ Ubuntu 22.04 сервер с установленным Docker и Docker Compose
- ✅ GitHub аккаунт с доступом к репозиторию
- ✅ Доменное имя с настроенным DNS
- ✅ SSH доступ к серверу

---

## Шаг 1: Подготовка сервера

### 1.1. Подключитесь к серверу

```bash
ssh root@YOUR_SERVER_IP
```

### 1.2. Обновите систему и установите Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose v2
sudo apt install docker-compose-plugin -y

# Проверка
docker --version
docker compose version
```

### 1.3. Установите Git

```bash
sudo apt install git -y
git --version
```

### 1.4. Создайте пользователя для деплоя (рекомендуется)

```bash
# Создать пользователя deploy
sudo adduser deploy

# Добавить в группу docker
sudo usermod -aG docker deploy

# Переключиться на пользователя deploy
su - deploy
```

---

## Шаг 2: Настройка SSH-ключей

### 2.1. Генерация SSH-ключа на сервере (если еще не создан)

```bash
# От имени пользователя deploy (или root)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy

# Просмотр публичного ключа
cat ~/.ssh/github_deploy.pub
```

### 2.2. Добавление публичного ключа в authorized_keys

```bash
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 2.3. Сохранение приватного ключа

```bash
# Скопируйте содержимое приватного ключа
cat ~/.ssh/github_deploy

# Сохраните вывод — он понадобится для GitHub Secrets
```

⚠️ **Важно**: Приватный ключ должен начинаться с `-----BEGIN OPENSSH PRIVATE KEY-----`

---

## Шаг 3: Первоначальный клон репозитория на сервере

### 3.1. Клонирование репозитория

```bash
# Переключитесь на пользователя deploy (если еще не сделали)
su - deploy

# Клонирование в /opt
cd /opt
sudo mkdir -p dudonya-vpn
sudo chown deploy:deploy dudonya-vpn

# Клонируйте ваш репозиторий
git clone https://github.com/YOUR_USERNAME/dudonya-vpn.git dudonya-vpn
cd dudonya-vpn
```

**Если репозитори�� приватный**, настройте SSH-ключ для GitHub:

```bash
# Создайте новый SSH-ключ для GitHub
ssh-keygen -t ed25519 -C "server-github" -f ~/.ssh/github_server

# Добавьте публичный ключ в GitHub
cat ~/.ssh/github_server.pub
# Скопируйте и добавьте в Settings > SSH Keys на GitHub

# Настройте SSH config
cat >> ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_server
EOF

chmod 600 ~/.ssh/config
```

### 3.2. Настройка .env файла

```bash
cd /opt/dudonya-vpn

# Создайте .env из примера
cp .env.example .env

# Отредактируйте .env
nano .env
```

**Обязательно заполните:**

```env
# Telegram
BOT_TOKEN=YOUR_REAL_BOT_TOKEN
BOT_USERNAME=your_bot_username
ADMIN_ID=YOUR_TELEGRAM_ID

# Domain
DOMAIN=https://your-domain.com

# Payment providers
CRYPTOBOT_TOKEN=your_cryptobot_token
FREEKASSA_SHOP_ID=your_shop_id
FREEKASSA_SECRET_WORD_1=your_secret_1
FREEKASSA_SECRET_WORD_2=your_secret_2
```

### 3.3. Настройка Caddyfile

```bash
nano Caddyfile
```

Замените `vpn.example.com` на ваш реальный домен и `admin@example.com` на ваш email.

### 3.4. Добавление VPN-конфигов

```bash
# Создайте файл с вашими VPN-конфигами
nano configs/servers.json
```

Пример:
```json
{
  "configs": [
    "vless://{{UUID}}@your-server.com:443?type=tcp&security=tls&sni=your-server.com#Dudonya-VPN-{{SHORT_ID}}"
  ]
}
```

### 3.5. Первоначальный запуск

```bash
# Инициализация базы данных
docker compose run --rm backend python scripts/init_db.py

# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f
```

Убедитесь, что все работает:
```bash
curl http://localhost:8000/health
```

---

## Шаг 4: Настройка GitHub Secrets

### 4.1. Откройте Settings в вашем репозитории на GitHub

```
GitHub Repository > Settings > Secrets and variables > Actions > New repository secret
```

### 4.2. Добавьте следующие secrets:

| Secret Name | Значение | Описание |
|-------------|----------|----------|
| `SERVER_HOST` | `123.45.67.89` | IP-адрес вашего сервера |
| `SERVER_USER` | `deploy` | Пользователь для SSH (deploy или root) |
| `SSH_PRIVATE_KEY` | *содержимое приватного ключа* | Приватный ключ из `~/.ssh/github_deploy` |
| `SSH_PORT` | `22` | SSH порт (опционально, по умолчанию 22) |
| `DEPLOY_PATH` | `/opt/dudonya-vpn` | Путь к проекту на сервере |

**Пример добавления SSH_PRIVATE_KEY:**

1. Нажмите **New repository secret**
2. Name: `SSH_PRIVATE_KEY`
3. Secret: Вставьте **весь** вывод `cat ~/.ssh/github_deploy`, включая:
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQ...
   ...
   -----END OPENSSH PRIVATE KEY-----
   ```
4. Нажмите **Add secret**

Повторите для остальных secrets.

---

## Шаг 5: Тестирование автоматического деплоя

### 5.1. Сделайте тестовое изменение

На вашем локальном компьютере:

```bash
# Клонируйте репозиторий (если еще не сделали)
git clone https://github.com/YOUR_USERNAME/dudonya-vpn.git
cd dudonya-vpn

# Внесите тестовое изменение
echo "# Test deployment" >> README.md

# Закоммитьте и запушьте
git add README.md
git commit -m "test: GitHub Actions deployment"
git push origin main
```

### 5.2. Проверьте выполнение workflow

1. Откройте **Actions** в вашем GitHub репозитории
2. Вы увидите запущенный workflow "Deploy to Production"
3. Кликните на него, чтобы увидеть логи
4. Дождитесь завершения (обычно 2-3 минуты)

### 5.3. Проверьте сервер

```bash
# Подключитесь к серверу
ssh deploy@YOUR_SERVER_IP

# Проверьте статус контейнеров
cd /opt/dudonya-vpn
docker compose ps

# Проверьте последний коммит
git log -1

# Проверьте здоровье backend
curl http://localhost:8000/health
```

✅ **Если всё работает — поздравляем! Автоматический деплой настроен.**

---

## 🔧 Ручной деплой через GitHub Actions

Вы можете запустить деплой вручную, не делая коммит:

1. Откройте **Actions** в GitHub
2. Выберите workflow "Deploy to Production"
3. Нажмите **Run workflow**
4. Выберите ветку `main`
5. Нажмите **Run workflow**

---

## 📊 Мониторинг и логи

### Просмотр логов на сервере

```bash
# Все логи
docker compose logs -f

# Только backend
docker compose logs -f backend

# Только bot
docker compose logs -f bot

# Последние 100 строк
docker compose logs --tail=100
```

### Проверка здоровья сервисов

```bash
# Health check
curl https://your-domain.com/health

# Статус контейнеров
docker compose ps

# Использование ресурсов
docker stats
```

---

## ⚠️ Troubleshooting

### Проблема: SSH connection failed

**Ошибка в GitHub Actions:**
```
Error: Cannot establish SSH connection
```

**Решение:**

1. Проверьте, что `SSH_PRIVATE_KEY` скопирован полностью
2. Проверьте, что публичный ключ добавлен в `~/.ssh/authorized_keys` на сервере
3. Проверьте, что SSH работает вручную:
   ```bash
   ssh -i ~/.ssh/github_deploy deploy@YOUR_SERVER_IP
   ```
4. Проверьте, что файрвол разрешает SSH:
   ```bash
   sudo ufw status
   sudo ufw allow 22/tcp
   ```

### Проблема: Permission denied (Git pull)

**Ошибка:**
```
Permission denied (publickey)
```

**Решение:**

Если репозиторий приватный, настройте SSH-ключ для GitHub на сервере (см. Шаг 3.1).

### Проблема: Docker build failed

**Ошибка:**
```
Error building image
```

**Решение:**

1. Проверьте логи на сервере:
   ```bash
   docker compose logs
   ```
2. Проверьте, что все файлы на месте:
   ```bash
   ls -la /opt/dudonya-vpn
   ```
3. Пересоберите вручную:
   ```bash
   docker compose build --no-cache
   ```

### Проблема: Services not starting

**Решение:**

```bash
# Проверьте статус
docker compose ps

# Перезапустите проблемный сервис
docker compose restart backend

# Проверьте .env файл
cat .env

# Убедитесь, что все переменные заполнены
```

### Проблема: Webhook not working

Если платежи не обрабатываются:

1. Проверьте, что webhook URL настроен в платежной системе:
   - CryptoBot: `https://your-domain.com/webhook/cryptobot`
   - Freekassa: `https://your-domain.com/webhook/freekassa`

2. Проверьте логи backend:
   ```bash
   docker compose logs -f backend | grep webhook
   ```

3. Проверьте, что домен доступен извне:
   ```bash
   curl -I https://your-domain.com/health
   ```

---

## 🔐 Безопасность

### Рекомендации:

1. **Используйте отдельного пользователя** для деплоя (не root)
2. **Храните .env в секрете** — не коммитьте его в Git
3. **Регулярно обновляйте** систему и Docker
4. **Настройте файрвол** (ufw):
   ```bash
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```
5. **Используйте SSH-ключи**, отключите пароли:
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Установите: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

---

## 📝 Workflow кастомизация

Вы можете изменить `.github/workflows/deploy.yml` под свои нужды:

### Деплой только при наличии тега

```yaml
on:
  push:
    tags:
      - 'v*'
```

### Уведомления в Telegram

Добавьте в конец workflow:

```yaml
      - name: Send Telegram notification
        if: always()
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          message: |
            🚀 Deployment ${{ job.status }}
            Repository: ${{ github.repository }}
            Commit: ${{ github.sha }}
```

Добавьте secrets `TELEGRAM_CHAT_ID` и `TELEGRAM_BOT_TOKEN`.

---

## ✅ Чек-лист успешной настройки

- [ ] Docker и Docker Compose установлены на сервере
- [ ] Репозиторий склонирован в `/opt/dudonya-vpn`
- [ ] `.env` файл настроен с реальными токенами
- [ ] `Caddyfile` обновлен с вашим доменом
- [ ] VPN-конфиги добавлены в `configs/servers.json`
- [ ] База данных инициализирована
- [ ] Контейнеры запущены и работают
- [ ] SSH-ключи настроены
- [ ] GitHub Secrets добавлены (все 5)
- [ ] Тестовый деплой успешно выполнен
- [ ] Backend отвечает на `/health`
- [ ] Бот отвечает на `/start`
- [ ] SSL-сертификат получен (Caddy)

---

## 🎉 Готово!

Теперь каждый push в `main` автоматически деплоится на ваш сервер.

**Дальнейшие шаги:**

1. Настройте webhook'и в платежных системах
2. Протестируйте покупку подписки
3. Настройте мониторинг (Uptime Kuma, Prometheus)
4. Настройте автоматические бэкапы БД

**Поддержка:**

- 📧 Email: support@dudonya.online
- 💬 Telegram: @dudonya_support

---

**Успешного деплоя! 🚀**
