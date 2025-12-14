# 🚀 Быстрый старт деплоя на Railway

## ✅ Что готово

- ✅ PostgreSQL модели (User, AuthRefreshToken, VerificationCode)
- ✅ Миграции Alembic (001_initial_migration.py)
- ✅ Auth endpoints (register, login, verify-email, forgot-password, reset-password)
- ✅ Email service с HTML шаблонами
- ✅ JWT токены (access + refresh)
- ✅ Автоматическое преобразование DATABASE_URL от Railway

## 📋 Шаги деплоя

### 1. Push кода в GitHub

```bash
cd /Users/mistadrumma/develop/cursor/survey-assessment-backend
git add .
git commit -m "Add PostgreSQL auth system with migrations"
git push origin main
```

### 2. Создание проекта на Railway

1. Зайдите на [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo**
3. Выберите: `rbr-ntc/survey-assessment-backend`
4. Railway автоматически определит Dockerfile

### 3. Добавление PostgreSQL

1. В проекте Railway: **New** → **Database** → **PostgreSQL**
2. Railway автоматически создаст переменные:
   - `DATABASE_URL` (будет автоматически преобразован в `POSTGRES_URL`)
   - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

### 4. Настройка переменных окружения

В **Settings → Variables** добавьте (см. `ENV_RAILWAY.md` для полного списка):

**Минимум для работы:**
```bash
API_KEY=<сгенерируйте: openssl rand -hex 32>
SECRET_KEY=<сгенерируйте: openssl rand -hex 64>
MONGO_URL=<ваш MongoDB URL>
OPENAI_API_KEY=<ваш OpenAI ключ>
CORS_ORIGINS=https://your-frontend.vercel.app
```

**POSTGRES_URL** автоматически создастся из `DATABASE_URL` от Railway, но можно указать явно:
```bash
POSTGRES_URL=postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
```

### 5. Применение миграций

После первого деплоя:

**Вариант 1: Railway CLI**
```bash
npm i -g @railway/cli
railway login
railway link
railway run alembic upgrade head
```

**Вариант 2: Railway Shell**
1. Railway Dashboard → ваш сервис → **Shell**
2. Выполните: `alembic upgrade head`

### 6. Проверка

1. Health check: `https://your-backend.railway.app/health`
2. Swagger docs: `https://your-backend.railway.app/docs`
3. Auth endpoints: `https://your-backend.railway.app/api/v1/auth/register`

## 🔧 Настройка Email (опционально)

Если не настроите SMTP, регистрация будет работать, но коды верификации не будут отправляться.

Добавьте в Railway Variables:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<Gmail App Password>
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=LearnHub LMS
```

**Gmail App Password:**
1. Включите 2FA в Google Account
2. Создайте App Password: https://myaccount.google.com/apppasswords
3. Используйте как `SMTP_PASSWORD`

## 📚 Документация

- Полный список переменных: `ENV_RAILWAY.md`
- Детальная инструкция: `RAILWAY_SETUP.md`
- API документация: `https://your-backend.railway.app/docs`

## ✅ Чеклист

- [ ] Код запушен в GitHub
- [ ] Проект создан на Railway
- [ ] PostgreSQL добавлен
- [ ] Все переменные окружения добавлены
- [ ] Миграции применены (`alembic upgrade head`)
- [ ] Health endpoint работает
- [ ] Swagger docs доступны
- [ ] Email SMTP настроен (опционально)

---

**Готово к деплою! 🚀**

