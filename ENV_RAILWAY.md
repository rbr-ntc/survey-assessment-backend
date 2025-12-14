# 🔧 Переменные окружения для Railway

## 📋 Полный список переменных

Скопируйте эти переменные в **Railway Dashboard → Ваш сервис → Settings → Variables**

### 🔴 Обязательные переменные

```bash
# API Configuration
API_KEY=your-secret-api-key-min-32-chars-generate-random
SECRET_KEY=your-very-secret-jwt-key-min-64-chars-generate-random

# PostgreSQL (Railway автоматически создаст DATABASE_URL)
# Config автоматически преобразует DATABASE_URL в POSTGRES_URL
# Но можно указать явно:
POSTGRES_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}

# MongoDB
MONGO_URL=mongodb://username:password@host:port/database?authSource=admin

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-5-mini
OPENAI_MAX_TOKENS=4000
OPENAI_REASONING_EFFORT=medium

# CORS (обновить после деплоя фронтенда)
CORS_ORIGINS=https://your-frontend.vercel.app
```

### 🟡 JWT и Security

```bash
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 🟢 Email (SMTP) - опционально

Если не настроите, email отправляться не будут, но регистрация будет работать:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=LearnHub LMS
```

**Для Gmail:**
1. Включите 2FA в Google Account
2. Создайте App Password: https://myaccount.google.com/apppasswords
3. Используйте App Password как `SMTP_PASSWORD`

### 🔵 Verification Codes

```bash
VERIFICATION_CODE_EXPIRE_MINUTES=15
```

### 🟣 Features

```bash
ENABLE_QUICK_TEST=true
```

### ⚪ Optional

```bash
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
LOG_LEVEL=INFO
```

---

## 🎯 Как Railway автоматически создает DATABASE_URL

Когда вы добавляете PostgreSQL в Railway:

1. Railway создает сервис PostgreSQL
2. Автоматически создает переменные:
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`
   - `DATABASE_URL=postgresql://user:pass@host:port/db`

3. **Наш код автоматически преобразует** `DATABASE_URL` в формат `postgresql+asyncpg://...` для SQLAlchemy async

**Важно:** Если Railway не создал `DATABASE_URL`, можно использовать:
```bash
POSTGRES_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
```

---

## 🔐 Генерация секретных ключей

### API_KEY (минимум 32 символа):
```bash
openssl rand -hex 32
```

### SECRET_KEY (минимум 64 символа):
```bash
openssl rand -hex 64
```

Или используйте онлайн генератор: https://randomkeygen.com/

---

## ✅ Чеклист настройки

- [ ] PostgreSQL сервис добавлен в Railway
- [ ] `DATABASE_URL` автоматически создан Railway (или `POSTGRES_URL` указан вручную)
- [ ] `API_KEY` сгенерирован и добавлен
- [ ] `SECRET_KEY` сгенерирован и добавлен
- [ ] `MONGO_URL` настроен
- [ ] `OPENAI_API_KEY` добавлен
- [ ] `CORS_ORIGINS` указан (можно обновить после деплоя фронтенда)
- [ ] Email SMTP настроен (опционально)
- [ ] Все остальные переменные добавлены

---

## 🚀 После настройки переменных

1. **Примените миграции:**
   ```bash
   railway run alembic upgrade head
   ```

2. **Проверьте health endpoint:**
   ```
   https://your-backend.railway.app/health
   ```

3. **Проверьте Swagger docs:**
   ```
   https://your-backend.railway.app/docs
   ```

4. **Проверьте auth endpoints:**
   ```
   https://your-backend.railway.app/api/v1/auth/register
   ```

