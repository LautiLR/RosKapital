"""
Sistema de caché con Redis
"""
import json
import redis
from typing import Any, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Conexión a Redis
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Conexión a Redis exitosa")
except Exception as e:
    logger.warning(f"⚠️ Redis no disponible: {e}. El caché estará deshabilitado.")
    redis_client = None


def cache_get(key: str) -> Optional[Any]:
    """Obtiene un valor del caché"""
    if not redis_client:
        return None
    
    try:
        value = redis_client.get(f"fintech:{key}")
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Error obteniendo del caché '{key}': {e}")
        return None


def cache_set(key: str, value: Any, expire: int = settings.CACHE_EXPIRE_SECONDS) -> bool:
    """Guarda un valor en el caché"""
    if not redis_client:
        return False
    
    try:
        serialized = json.dumps(value)
        redis_client.setex(f"fintech:{key}", expire, serialized)
        return True
    except Exception as e:
        logger.error(f"Error guardando en caché '{key}': {e}")
        return False


def cache_delete(key: str) -> bool:
    """Elimina un valor del caché"""
    if not redis_client:
        return False
    
    try:
        redis_client.delete(f"fintech:{key}")
        return True
    except Exception as e:
        logger.error(f"Error eliminando del caché '{key}': {e}")
        return False


def cache_clear_pattern(pattern: str) -> int:
    """Elimina todas las keys que coincidan con un patrón"""
    if not redis_client:
        return 0
    
    try:
        keys = redis_client.keys(f"fintech:{pattern}")
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Error limpiando caché con patrón '{pattern}': {e}")
        return 0


def cache_exists(key: str) -> bool:
    """Verifica si una key existe en el caché"""
    if not redis_client:
        return False
    
    try:
        return redis_client.exists(f"fintech:{key}") > 0
    except Exception as e:
        logger.error(f"Error verificando existencia en caché '{key}': {e}")
        return False
