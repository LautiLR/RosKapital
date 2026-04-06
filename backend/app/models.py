"""
Modelos de base de datos SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Modelo de Usuario"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Perfil de inversor
    investor_profile = Column(String(50), nullable=True)  # Don Horacio, Valeria, Enzo
    portfolio_public = Column(Boolean, default=False)
    streak_count = Column(Integer, default=0)
    last_visit_date = Column(String(10), nullable=True)  # formato YYYY-MM-DD
    
    # Estado
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relaciones
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    """Portfolio del simulador"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Datos del portfolio
    initial_capital = Column(Float, default=100000.0)
    current_equity = Column(Float, default=100000.0)
    cash_available = Column(Float, default=100000.0)
    portfolio_profile = Column(String(50), nullable=True)  # Agresivo, Equilibrado, Defensivo
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")


class Position(Base):
    """Posición abierta en el portfolio"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Datos de la posición
    ticker = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    
    # Asset info
    asset_type = Column(String(20), default="stock")  # stock, crypto
    asset_name = Column(String(255), nullable=True)
    
    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    portfolio = relationship("Portfolio", back_populates="positions")


class Trade(Base):
    """Historial de trades"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    
    # Datos del trade
    ticker = Column(String(20), nullable=False, index=True)
    trade_type = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Asset info
    asset_type = Column(String(20), default="stock")
    asset_name = Column(String(255), nullable=True)
    
    # Timestamp
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relaciones
    user = relationship("User", back_populates="trades")


class Watchlist(Base):
    """Lista de seguimiento de activos"""
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Datos
    ticker = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20), default="stock")
    asset_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Alertas (opcional)
    alert_enabled = Column(Boolean, default=False)
    alert_price_above = Column(Float, nullable=True)
    alert_price_below = Column(Float, nullable=True)
    
    # Timestamp
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="watchlists")


class EquitySnapshot(Base):
    """Snapshots del equity para gráficos históricos"""
    __tablename__ = "equity_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Datos
    equity = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    invested = Column(Float, nullable=False)
    
    # Timestamp
    snapshot_at = Column(DateTime, default=datetime.utcnow, index=True)


class Mission(Base):
    """Sistema de misiones/logros"""
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Datos de la misión
    mission_key = Column(String(50), nullable=False)  # identidad, explorador, inversor, etc.
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    """API Keys para acceso programático (opcional)"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Key
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_name = Column(String(100), nullable=False)
    
    # Permisos
    is_active = Column(Boolean, default=True)
    read_only = Column(Boolean, default=True)
    
    # Rate limits específicos
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
class Post(Base):
    """Posts del blog de la comunidad"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Autor (sin necesidad de cuenta)
    autor_nombre = Column(String(100), nullable=False)
    
    # Contenido
    titulo = Column(String(255), nullable=False)
    contenido = Column(Text, nullable=False)
    tag = Column(String(50), nullable=False)  # Análisis, Merval, Crypto, CEDEARs, Consulta, Opinión, Educativo
    imagen_url = Column(String(500), nullable=True)
    
    # Métricas
    likes = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relaciones
    comentarios = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    """Comentarios en posts"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    
    # Autor (sin necesidad de cuenta)
    autor_nombre = Column(String(100), nullable=False)
    
    # Contenido
    contenido = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    post = relationship("Post", back_populates="comentarios")
    
class VerificationCode(Base):
    """Códigos de verificación por email"""
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

class Alert(Base):
    """Alertas de precio"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    precio = Column(Float, nullable=False)
    direccion = Column(String(10), nullable=False)  # above, below
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Notification(Base):
    """Notificaciones in-app"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    tipo = Column(String(30), nullable=False)  # alerta_precio, mision, comunidad, sistema
    titulo = Column(String(200), nullable=False)
    mensaje = Column(String(500), nullable=False)
    link = Column(String(255), nullable=True)  # URL a la que lleva al clickear
    
    leida = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)