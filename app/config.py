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
    
    # CORS
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # OpenAI
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_REASONING_EFFORT: str = "medium"  # none, low, medium, high
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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
