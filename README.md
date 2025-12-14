# Survey Assessment Backend

FastAPI backend для системы оценки системных аналитиков с AI-рекомендациями.

## 🚀 Технологии

- **FastAPI** - современный веб-фреймворк для Python
- **MongoDB** - NoSQL база данных
- **OpenAI API** - генерация AI-рекомендаций (GPT-5.2-mini)
- **Pydantic** - валидация данных
- **Uvicorn** - ASGI сервер

## 📋 Требования

- Python 3.10+
- MongoDB 6.0+
- OpenAI API ключ

## 🔧 Установка

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

## ⚙️ Настройка

Создайте файл `.env` в корне проекта:

```env
API_KEY=your-secret-api-key
SECRET_KEY=your-secret-key-for-jwt
OPENAI_API_KEY=sk-proj-...
MONGO_URL=mongodb://localhost:27017/assessment
CORS_ORIGINS=http://localhost:3000
ENABLE_QUICK_TEST=true
OPENAI_MODEL=gpt-5.2-mini
OPENAI_MAX_TOKENS=4000
OPENAI_REASONING_EFFORT=medium
```

## 🏃 Запуск

```bash
# Запуск в режиме разработки
uvicorn app.main:app --reload

# Запуск в продакшене
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API будет доступен по адресу: `http://localhost:8000`

Документация API: `http://localhost:8000/docs`

## 🐳 Docker

```bash
# Сборка образа
docker build -t survey-assessment-backend .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env survey-assessment-backend
```

## 🧪 Тестирование

```bash
# Запуск тестов
pytest

# С покрытием
pytest --cov=app tests/
```

## 📚 API Endpoints

- `GET /health` - Health check
- `GET /questions` - Получить список вопросов
- `POST /results` - Отправить результаты теста
- `GET /results/{id}` - Получить результат по ID
- `POST /recommendations` - Сгенерировать AI-рекомендации
- `POST /quick-test` - Быстрый тест (если включен)

## 🚂 Деплой на Railway

1. Создайте проект на [Railway](https://railway.app)
2. Подключите этот репозиторий
3. Установите Root Directory: `backend` (если репозиторий содержит только backend)
4. Добавьте все переменные окружения из `.env`
5. Railway автоматически задеплоит приложения

## 📝 Лицензия

MIT
