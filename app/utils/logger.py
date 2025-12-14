import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.config import settings


class JSONFormatter(logging.Formatter):
    """Форматтер для логирования в JSON формате"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем дополнительные поля если есть
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Добавляем exception info если есть
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Настройка логгера с JSON форматированием"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(level or settings.LOG_LEVEL)
    return logger

def log_request(logger: logging.Logger, method: str, path: str, status_code: int, 
                process_time: float, client_ip: str, **extra_fields):
    """Логирование HTTP запроса"""
    logger.info(
        "HTTP Request",
        extra={
            "extra_fields": {
                "type": "http_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "client_ip": client_ip,
                **extra_fields
            }
        }
    )

def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Логирование ошибок с контекстом"""
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "extra_fields": {
                "type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {}
            }
        },
        exc_info=True
    )

def log_performance(logger: logging.Logger, operation: str, duration: float, 
                   metadata: Dict[str, Any] = None):
    """Логирование производительности операций"""
    logger.info(
        f"Performance: {operation}",
        extra={
            "extra_fields": {
                "type": "performance",
                "operation": operation,
                "duration_ms": round(duration * 1000, 2),
                "metadata": metadata or {}
            }
        }
    )
