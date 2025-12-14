# 🚂 Деплой на Railway - Пошаговая инструкция

## Шаг 1: Push кода в GitHub ✅

Код уже запушен в репозиторий `rbr-ntc/survey-assessment-backend`.

## Шаг 2: Создание проекта на Railway

1. Зайдите на [railway.app](https://railway.app)
2. Войдите в аккаунт (или создайте новый)
3. Нажмите **New Project**
4. Выберите **Deploy from GitHub repo**
5. Выберите репозиторий: `rbr-ntc/survey-assessment-backend`
6. Railway автоматически определит Dockerfile и начнет деплой

## Шаг 3: Добавление PostgreSQL базы данных

1. В проекте Railway нажмите **New** → **Database** → **PostgreSQL**
2. Railway автоматически создаст PostgreSQL сервис
3. Подождите, пока база данных будет создана (1-2 минуты)
4. Railway автоматически создаст переменные окружения:
   - `DATABASE_URL` (будет автоматически преобразован в `POSTGRES_URL`)
   - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

## Шаг 4: Настройка переменных окружения

В настройках вашего сервиса (Settings → Variables) добавьте:

### Обязательные переменные:

```bash
# API Configuration
API_KEY=<сгенерируйте: openssl rand -hex 32>
SECRET_KEY=<сгенерируйте: openssl rand -hex 64>

# MongoDB (если еще не добавлен)
MONGO_URL=mongodb://username:password@host:port/database?authSource=admin

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-5-mini
OPENAI_MAX_TOKENS=4000
OPENAI_REASONING_EFFORT=medium

# CORS (обновить после деплоя фронтенда)
CORS_ORIGINS=https://your-frontend.vercel.app

# JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Verification codes
VERIFICATION_CODE_EXPIRE_MINUTES=15

# Features
ENABLE_QUICK_TEST=true

# Optional
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
LOG_LEVEL=INFO
```

**Важно:** `POSTGRES_URL` автоматически создастся из `DATABASE_URL`, но можно указать явно:
```bash
POSTGRES_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
```

### Email (опционально, но рекомендуется):

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<Gmail App Password>
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=LearnHub LMS
```

## Шаг 5: Применение миграций

После того как все переменные настроены и сервис задеплоен:

### Вариант 1: Через Railway CLI (рекомендуется)

```bash
# Установите Railway CLI (если еще не установлен)
npm i -g @railway/cli

# Войдите в Railway
railway login

# Подключитесь к проекту
railway link

# Выберите проект и сервис когда Railway спросит

# Примените миграции
railway run alembic upgrade head
```

### Вариант 2: Через Railway Shell

1. В Railway Dashboard откройте ваш сервис
2. Перейдите в раздел **Shell** (или **Deployments** → выберите последний деплой → **Shell**)
3. Выполните команду:
```bash
alembic upgrade head
```

### Вариант 3: Через скрипт

```bash
railway run bash railway_migrations.sh
```

## Шаг 6: Проверка деплоя

1. **Health check:**
   ```
   https://your-backend.railway.app/health
   ```
   Должен вернуть: `{"status": "healthy", ...}`

2. **Swagger документация:**
   ```
   https://your-backend.railway.app/docs
   ```
   Должна открыться интерактивная документация API

3. **Auth endpoints:**
   ```
   POST https://your-backend.railway.app/api/v1/auth/register
   GET https://your-backend.railway.app/api/v1/auth/me
   ```

## Шаг 7: Получение URL бэкенда

1. В Railway Dashboard откройте ваш сервис
2. Перейдите в **Settings** → **Networking**
3. Скопируйте **Public Domain** (например: `your-backend.railway.app`)
4. Или настройте кастомный домен в **Custom Domain**

## 🔧 Troubleshooting

### Ошибка: "No module named 'alembic'"
**Решение:** Убедитесь, что `alembic` в `requirements.txt` (уже добавлен)

### Ошибка: "relation does not exist"
**Решение:** Примените миграции: `railway run alembic upgrade head`

### Ошибка: "Invalid URL format"
**Решение:** Проверьте, что `POSTGRES_URL` имеет формат `postgresql+asyncpg://...`

### Ошибка: "Connection refused"
**Решение:** Проверьте, что PostgreSQL сервис запущен в Railway

### Ошибка при деплое: "ModuleNotFoundError"
**Решение:** Проверьте, что все зависимости в `requirements.txt` и код правильно структурирован

## ✅ Чеклист

- [ ] Проект создан на Railway
- [ ] Репозиторий подключен
- [ ] PostgreSQL база данных добавлена
- [ ] Все переменные окружения добавлены
- [ ] Сервис успешно задеплоен
- [ ] Миграции применены (`alembic upgrade head`)
- [ ] Health endpoint работает
- [ ] Swagger docs доступны
- [ ] Auth endpoints работают

---

**Готово! 🎉**

После успешного деплоя можно переходить к созданию frontend компонентов с glassmorphism дизайном.

