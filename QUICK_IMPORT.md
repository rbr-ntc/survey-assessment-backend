# Быстрый импорт вопросов в MongoDB на Railway

## 🚀 Самый простой способ

### Через Railway CLI:

1. **Установите Railway CLI:**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Подключите проект:**
   ```bash
   cd survey-assessment-backend
   railway link
   ```

3. **Импортируйте вопросы:**
   ```bash
   # Установите переменную MONGO_URL из Railway
   railway variables
   
   # Или импортируйте напрямую через Railway shell
   railway run python import_questions.py
   ```

### Или через MongoDB Compass:

1. **Получите MONGO_URL из Railway:**
   - Railway Dashboard → Ваш проект → MongoDB сервис
   - Settings → Variables → MONGO_URL
   - Скопируйте строку подключения

2. **Откройте MongoDB Compass:**
   - Вставьте MONGO_URL
   - Подключитесь

3. **Импортируйте данные:**
   - База данных: `assessment`
   - Коллекция: `questions`
   - Import Data → `improved-test-questions.json`
   - Format: JSON Array

### Или через mongoimport (если установлен MongoDB CLI):

```bash
# Получите MONGO_URL из Railway
MONGO_URL="your-mongo-url-here"

# Импортируйте
mongoimport --uri="$MONGO_URL" \
  --db=assessment \
  --collection=questions \
  --file=improved-test-questions.json \
  --jsonArray
```

## ✅ Проверка

После импорта проверьте через API:

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  https://your-backend.railway.app/questions
```

Должен вернуться массив вопросов, а не 404!

