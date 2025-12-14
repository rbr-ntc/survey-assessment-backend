import logging
import os
import time

from app.config import settings
from app.routers import questions, recommendations, results
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="System Analyst Assessment API",
    description="API для оценки системных аналитиков с AI рекомендациями",
    version="1.0.0"
)

# Добавляем middleware используя декораторы
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def add_logging_middleware(request: Request, call_next):
    # Логируем начало запроса
    logger.info(f"Request started: {request.method} {request.url.path}")
    
    # Выполняем запрос
    response = await call_next(request)
    
    # Логируем результат
    logger.info(f"Request completed: {request.method} {request.url.path} -> {response.status_code}")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck"""
    logger.info("Health check requested")
    return {
        "status": "healthy", 
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
        "environment": "production"
    }

app.include_router(questions.router)
app.include_router(results.router)
app.include_router(recommendations.router)
