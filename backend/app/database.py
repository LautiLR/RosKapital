"""
Configuración de base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa la base de datos (crea tablas)"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
