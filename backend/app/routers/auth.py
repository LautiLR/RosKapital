"""
Router de Autenticación
Endpoints para registro, login, y gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from app.models import Position, Trade, Watchlist, Mission, Alert

from app.database import get_db
from app.models import User, Portfolio
from app.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    get_current_user,
    verify_token
)

router = APIRouter()


# ============================================
# SCHEMAS
# ============================================

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    investor_profile: str | None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# ENDPOINTS
# ============================================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Registra un nuevo usuario y envía código de verificación"""
    from app.models import VerificationCode
    from app.auth import generate_verification_code, send_verification_email
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    validate_password_strength(user_data.password)
    
    # Crear usuario no verificado
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Crear portfolio inicial
    initial_portfolio = Portfolio(
        user_id=new_user.id,
        initial_capital=100000.0,
        current_equity=100000.0,
        cash_available=100000.0
    )
    db.add(initial_portfolio)
    
    # Generar y guardar código
    code = generate_verification_code()
    verification = VerificationCode(
        email=user_data.email,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(verification)
    db.commit()
    
    # Enviar email
    send_verification_email(user_data.email, code)
    
    return {"message": "Cuenta creada. Revisá tu email para el código de verificación.", "email": user_data.email}

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Inicia sesión con email y contraseña"""
    
    user = authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email no verificado. Revisá tu casilla de correo."
        )
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Renueva el access token usando un refresh token"""
    
    payload = verify_token(refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )
    
    # Crear nuevo access token
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtiene información del usuario autenticado"""
    return current_user

class MigrateData(BaseModel):
    portfolio: list = []
    watchlist: list = []
    alertas: list = []
    misiones: list = []
    perfil_inversor: dict | None = None
    capital: float = 100000.0

@router.post("/migrate")
async def migrate_local_data(
    data: MigrateData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Migra datos de localStorage a la cuenta del usuario"""
    from app.models import Position, Trade, Watchlist, Mission
    
    # Solo migrar si el usuario no tiene datos previos
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id, initial_capital=data.capital, current_equity=data.capital, cash_available=data.capital)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    # Migrar posiciones
    existing_positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).count()
    if existing_positions == 0 and data.portfolio:
        for pos in data.portfolio:
            position = Position(
                portfolio_id=portfolio.id,
                ticker=pos.get('ticker', ''),
                quantity=pos.get('q', 0),
                average_price=pos.get('price', 0),
                asset_name=pos.get('nombre', '')
            )
            db.add(position)
    
    # Migrar watchlist
    existing_wl = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).count()
    if existing_wl == 0 and data.watchlist:
        for ticker in data.watchlist:
            wl = Watchlist(user_id=current_user.id, ticker=ticker)
            db.add(wl)
    
    # Migrar misiones
    existing_missions = db.query(Mission).filter(Mission.user_id == current_user.id).count()
    if existing_missions == 0 and data.misiones:
        for mission_key in data.misiones:
            mission = Mission(user_id=current_user.id, mission_key=mission_key, completed=True, completed_at=datetime.utcnow())
            db.add(mission)
    
    # Migrar perfil inversor
    if data.perfil_inversor and not current_user.investor_profile:
        current_user.investor_profile = data.perfil_inversor.get('tipo', '')
        
    existing_alerts = db.query(Alert).filter(Alert.user_id == current_user.id).count()
    if existing_alerts == 0 and data.alertas:
        for alerta in data.alertas:
            a = Alert(
                user_id=current_user.id,
                ticker=alerta.get('ticker', ''),
                precio=alerta.get('precio', 0),
                direccion=alerta.get('direccion', 'above')
            )
            db.add(a)
    
    db.commit()
    
    return {"message": "Datos migrados correctamente"}

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

@router.post("/verify", response_model=TokenResponse)
async def verify_email(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    """Verifica el código enviado por email"""
    from app.models import VerificationCode
    
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == data.email,
        VerificationCode.code == data.code,
        VerificationCode.used == False
    ).order_by(VerificationCode.created_at.desc()).first()
    
    if not verification:
        raise HTTPException(status_code=400, detail="Código inválido")
    
    if verification.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="El código expiró. Solicitá uno nuevo.")
    
    # Marcar como usado
    verification.used = True
    
    # Verificar usuario
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user.is_verified = True
    db.commit()
    
    # Crear tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    from app.models import Notification
    notif = Notification(
        user_id=user.id,
        tipo="sistema",
        titulo="¡Bienvenido a RosKapital!",
        mensaje="Tu cuenta está lista. Explorá el simulador, seguí activos y completá misiones.",
        link="/simulador"
    )
    db.add(notif)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/resend-code")
async def resend_code(email: EmailStr, db: Session = Depends(get_db)):
    """Reenvía el código de verificación"""
    from app.models import VerificationCode
    from app.auth import generate_verification_code, send_verification_email
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email no registrado")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email ya verificado")
    
    code = generate_verification_code()
    verification = VerificationCode(
        email=email,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(verification)
    db.commit()
    
    send_verification_email(email, code)
    
    return {"message": "Código reenviado"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Cierra sesión (en el cliente se debe eliminar el token)"""
    return {"message": "Sesión cerrada correctamente"}
