# 🚂 Настройка деплоя на Railway с PostgreSQL

## 📋 Шаги развертывания

### 1. Создание проекта на Railway

1. Зайдите на [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo**
3. Выберите репозиторий: `rbr-ntc/survey-assessment-backend`
4. Railway автоматически определит Dockerfile

### 2. Добавление PostgreSQL базы данных

1. В проекте Railway нажмите **New** → **Database** → **PostgreSQL**
2. Railway автоматически создаст PostgreSQL и предоставит переменные окружения:
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`
   - `DATABASE_URL` (полный URL)

3. **Важно:** Railway автоматически создаст переменную `DATABASE_URL`, но нам нужен формат для asyncpg:
   ```
   postgresql+asyncpg://user:password@host:port/database
   ```

### 3. Настройка переменных окружения

В настройках Backend сервиса (Settings → Variables) добавьте:

#### Обязательные переменные:

```bash
# API Configuration
API_KEY=your-secret-api-key-min-32-chars
SECRET_KEY=your-very-secret-jwt-key-min-64-chars-use-random-generator

# PostgreSQL (Railway автоматически создаст DATABASE_URL, но нужно преобразовать)
# Если Railway создал DATABASE_URL=postgresql://..., то:
POSTGRES_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
# ИЛИ используйте DATABASE_URL напрямую, заменив postgresql:// на postgresql+asyncpg://
# POSTGRES_URL=${DATABASE_URL/postgresql:\/\//postgresql+asyncpg:\/\/}

# MongoDB (если еще не добавлен)
MONGO_URL=mongodb://username:password@host:port/database?authSource=admin

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-5-mini
OPENAI_MAX_TOKENS=4000
OPENAI_REASONING_EFFORT=medium

# CORS (обновим после деплоя фронтенда)
CORS_ORIGINS=https://your-frontend.vercel.app

# JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (SMTP) - опционально, можно настроить позже
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=LearnHub LMS

# Verification codes
VERIFICATION_CODE_EXPIRE_MINUTES=15

# Features
ENABLE_QUICK_TEST=true

# Optional
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
LOG_LEVEL=INFO
```

### 4. Создание миграций (после первого деплоя)

После первого деплоя нужно создать и применить миграции:

**Вариант 1: Через Railway CLI (рекомендуется)**

```bash
# Установите Railway CLI
npm i -g @railway/cli

# Войдите в Railway
railway login

# Подключитесь к проекту
railway link

# Запустите миграции
railway run alembic upgrade head
```

**Вариант 2: Через Railway Shell**

1. В Railway Dashboard → ваш сервис → **Shell**
2. Выполните:
```bash
alembic upgrade head
```

**Вариант 3: Автоматически при старте (если добавить в startup)**

Можно добавить автоматический запуск миграций в `app/main.py`:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Run migrations
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
```

### 5. Проверка деплоя

1. После деплоя проверьте логи в Railway Dashboard
2. Проверьте health endpoint: `https://your-backend.railway.app/health`
3. Проверьте Swagger docs: `https://your-backend.railway.app/docs`

### 6. Импорт вопросов в MongoDB (если нужно)

Если нужно импортировать вопросы в MongoDB:

```bash
# Через Railway Shell
railway run python import_questions.py
```

---

## 🔧 Настройка PostgreSQL URL для asyncpg

Railway предоставляет переменные:
- `DATABASE_URL=postgresql://user:pass@host:port/db`

Но SQLAlchemy async требует формат:
- `postgresql+asyncpg://user:pass@host:port/db`

**Решение:** В Railway Variables добавьте:

```bash
POSTGRES_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
```

Или создайте скрипт преобразования в `app/config.py` (уже реализовано через `POSTGRES_URL`).

---

## 📝 Чеклист

- [ ] Проект создан на Railway
- [ ] PostgreSQL база данных добавлена
- [ ] Переменная `POSTGRES_URL` настроена (формат `postgresql+asyncpg://...`)
- [ ] Все переменные окружения добавлены
- [ ] Миграции применены (`alembic upgrade head`)
- [ ] Health endpoint работает
- [ ] Swagger docs доступны
- [ ] MongoDB настроен (если используется)
- [ ] Email SMTP настроен (опционально)

---

## 🐛 Troubleshooting

### Ошибка: "No module named 'asyncpg'"
**Решение:** Убедитесь, что `asyncpg` в `requirements.txt` (уже добавлен)

### Ошибка: "relation does not exist"
**Решение:** Примените миграции: `railway run alembic upgrade head`

### Ошибка: "Invalid URL format"
**Решение:** Проверьте формат `POSTGRES_URL` - должен быть `postgresql+asyncpg://...`

### Ошибка: "Connection refused"
**Решение:** Проверьте, что PostgreSQL сервис запущен в Railway

