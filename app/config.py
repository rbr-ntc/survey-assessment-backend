import os
from typing import List

from pydantic import BaseModel, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    API_KEY: str
    OPENAI_API_KEY: str
    
    # Database
    MONGO_URL: str
    POSTGRES_URL: str = ""  # postgresql+asyncpg://user:pass@host/dbname
    
    @validator('POSTGRES_URL', pre=True, always=True)
    def auto_convert_database_url(cls, v):
        """Auto-convert Railway DATABASE_URL to POSTGRES_URL format"""
        # If POSTGRES_URL is explicitly set, use it
        if v:
            return v
        
        # Otherwise, try to convert DATABASE_URL from Railway
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            # Convert postgresql:// to postgresql+asyncpg://
            if db_url.startswith("postgresql://"):
                return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgres://"):
                return db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            else:
                return db_url
        
        return ""
    
    # CORS
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # OpenAI
    OPENAI_MODEL: str = "gpt-5-mini"  # Available: gpt-5.1, gpt-5-mini, gpt-5-nano
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_REASONING_EFFORT: str = "medium"  # none, low, medium, high
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"
    
    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "LearnHub LMS"
    
    # Verification codes
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @validator('CORS_ORIGINS')
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"

settings = Settings()
