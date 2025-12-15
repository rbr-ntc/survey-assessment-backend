import logging
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.auth import router as auth_router
from app.config import settings
from app.limiter import limiter
from app.db_postgres import init_db
from app.routers import questions, quizzes, recommendations, results

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

# Set up Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Добавляем middleware используя декораторы
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

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

# Include routers
app.include_router(questions.router)
app.include_router(results.router)
app.include_router(recommendations.router)
app.include_router(quizzes.router)
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        logger.info("Starting database initialization...")
        logger.info(f"POSTGRES_URL configured: {bool(settings.POSTGRES_URL)}")
        
        # Initialize database (create tables if not exist)
        # Note: This is a fallback - migrations should be run via Alembic in start.sh
        await init_db()
        logger.info("Database initialized successfully")
        
        # Test database connection
        from app.db_postgres import get_session_factory
        session_factory = get_session_factory()
        async with session_factory() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        # Don't raise - let the app start, but log the error


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    from app.db_postgres import close_db
    await close_db()
    logger.info("Database connections closed")
