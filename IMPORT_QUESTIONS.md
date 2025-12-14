# Импорт вопросов в MongoDB на Railway

## Проблема

После деплоя на Railway MongoDB создается пустой, и вопросы нужно импортировать вручную.

## Решение

### Вариант 1: Через Railway MongoDB Shell (рекомендуется)

1. **Откройте Railway Dashboard:**

   - Зайдите на [railway.app](https://railway.app)
   - Откройте ваш проект
   - Найдите сервис MongoDB

2. **Откройте MongoDB Shell:**

   - В настройках MongoDB сервиса найдите "Connect"
   - Скопируйте строку подключения (MONGO_URL)
   - Или используйте встроенный MongoDB Shell в Railway

3. **Подключитесь к MongoDB:**

   ```bash
   # Если используете Railway CLI
   railway connect mongodb

   # Или используйте mongoimport напрямую с MONGO_URL
   ```

4. **Импортируйте вопросы:**
   ```bash
   # Убедитесь, что вы в директории с файлом improved-test-questions.json
   mongoimport --uri="YOUR_MONGO_URL" \
     --db=assessment \
     --collection=questions \
     --file=improved-test-questions.json \
     --jsonArray
   ```

### Вариант 2: Через MongoDB Compass или другой клиент

1. **Получите MONGO_URL из Railway:**

   - Settings → Variables → MONGO_URL
   - Скопируйте строку подключения

2. **Подключитесь через MongoDB Compass:**

   - Вставьте MONGO_URL
   - Подключитесь к базе данных

3. **Импортируйте данные:**
   - Выберите базу данных `assessment`
   - Выберите коллекцию `questions`
   - Import Data → Select File → `improved-test-questions.json`
   - Format: JSON Array
   - Import

### Вариант 3: Через скрипт Python (если есть доступ к контейнеру)

1. **Создайте временный скрипт импорта:**

   ```python
   import json
   import os
   from motor.motor_asyncio import AsyncIOMotorClient

   MONGO_URL = os.environ.get("MONGO_URL")
   client = AsyncIOMotorClient(MONGO_URL)
   db = client.assessment

   async def import_questions():
       with open("improved-test-questions.json", "r") as f:
           questions = json.load(f)

       await db.questions.insert_many(questions)
       print(f"Imported {len(questions)} questions")

   import asyncio
   asyncio.run(import_questions())
   ```

2. **Запустите скрипт:**
   ```bash
   python import_questions.py
   ```

### Вариант 4: Через Railway CLI (самый простой)

1. **Установите Railway CLI:**

   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Подключитесь к MongoDB:**

   ```bash
   cd survey-assessment-backend
   railway link  # Подключите проект
   railway connect mongodb  # Подключитесь к MongoDB
   ```

3. **Импортируйте вопросы:**

   ```bash
   # В MongoDB shell
   use assessment

   # Импортируйте через mongoimport
   # (нужно выйти из shell и использовать mongoimport)
   ```

## Проверка

После импорта проверьте, что вопросы загружены:

1. **Через API:**

   ```bash
   curl -H "x-api-key: YOUR_API_KEY" \
     https://your-backend.railway.app/questions
   ```

2. **Через MongoDB Shell:**
   ```javascript
   use assessment
   db.questions.count()
   ```

## Структура данных

Файл `improved-test-questions.json` должен содержать массив объектов вопросов:

```json
[
  {
    "id": 1,
    "category": "Requirements Analysis",
    "type": "multiple_choice",
    "question": "...",
    "options": [...]
  },
  ...
]
```

## Важно

- Убедитесь, что база данных называется `assessment`
- Коллекция должна называться `questions`
- Данные должны быть в формате JSON Array
- После импорта перезапустите backend сервис (если нужно)
