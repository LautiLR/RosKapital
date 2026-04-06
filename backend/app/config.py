"""
Configuración centralizada de la aplicación
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno"""
    
    # Application
    APP_NAME: str = "Fintech Advisor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    CACHE_EXPIRE_SECONDS: int = 300
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    COINGECKO_API_KEY: str = ""
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@fintechadvisor.com"
    
    # Sentry
    SENTRY_DSN: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Session
    SESSION_SECRET_KEY: str = ""
    SESSION_COOKIE_NAME: str = "fintech_session"
    SESSION_EXPIRE_MINUTES: int = 60
    
    # Security Headers
    ENABLE_HSTS: bool = True
    HSTS_MAX_AGE: int = 31536000
    
    # Internal
    INTERNAL_API_KEY: str = ""
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte string de CORS origins a lista"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene settings cacheados (singleton)"""
    return Settings()


# Exportar instancia global
settings = get_settings()
