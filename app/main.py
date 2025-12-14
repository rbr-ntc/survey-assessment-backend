import logging
import os
import time

from app.auth import router as auth_router
from app.config import settings
from app.db_postgres import init_db
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

# Include routers
app.include_router(questions.router)
app.include_router(results.router)
app.include_router(recommendations.router)
app.include_router(auth_router.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Run migrations automatically (optional - can be done manually via Railway CLI)
        # Uncomment if you want auto-migrations on startup
        # try:
        #     from alembic.config import Config
        #     from alembic import command
        #     alembic_cfg = Config("alembic.ini")
        #     command.upgrade(alembic_cfg, "head")
        #     logger.info("Migrations applied successfully")
        # except Exception as migration_error:
        #     logger.warning(f"Migrations not applied (this is OK if done manually): {migration_error}")
        
        # Initialize database (create tables if not exist)
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    from app.db_postgres import close_db
    await close_db()
    logger.info("Database connections closed")
