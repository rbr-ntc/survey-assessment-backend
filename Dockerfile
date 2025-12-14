# Простой Dockerfile для отладки
FROM python:3.10-slim

WORKDIR /app

# Принимаем build args для переменных окружения
ARG CORS_ORIGINS
ARG ENABLE_QUICK_TEST
ENV CORS_ORIGINS=$CORS_ORIGINS
ENV ENABLE_QUICK_TEST=$ENABLE_QUICK_TEST

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем alembic конфиг и миграции
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Startup script (runs migrations + starts uvicorn)
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# Копируем код приложения
COPY ./app ./app

# Railway использует переменную PORT, но для совместимости используем 8000 по умолчанию
ENV PORT=8000
EXPOSE $PORT

# Используем shell форму для правильного расширения переменной PORT
CMD ["sh", "-c", "./start.sh"] 