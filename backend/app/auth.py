"""
Sistema de autenticación y seguridad
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
import bcrypt


# Security scheme
security = HTTPBearer()


# ============================================
# PASSWORD HASHING
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# ============================================
# JWT TOKENS
# ============================================

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un access token JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """Crea un refresh token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Dict:
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================
# AUTHENTICATION DEPENDENCIES
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Obtiene el usuario actual desde el token"""
    
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id = int(payload.get("sub"))
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Token type validation
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica que el usuario esté activo"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


# ============================================
# OPTIONAL AUTHENTICATION
# ============================================

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Obtiene el usuario actual si está autenticado, sino retorna None"""
    
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ============================================
# USER AUTHENTICATION
# ============================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autentica un usuario con email y contraseña"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# ============================================
# PASSWORD VALIDATION
# ============================================

def validate_password_strength(password: str) -> bool:
    """Valida que la contraseña cumpla con requisitos mínimos"""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    
    # Al menos una letra mayúscula
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una letra mayúscula"
        )
    
    # Al menos un número
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un número"
        )
    
    return True

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

def generate_verification_code():
    return str(random.randint(100000, 999999))

def send_verification_email(to_email: str, code: str):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🔐 RosKapital - Tu código de verificación: {code}'
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = to_email
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; background: #0a0b0f; color: #e8eaed; padding: 2rem; border-radius: 16px;">
            <h2 style="text-align: center; margin-bottom: 0.5rem;">🔐 RosKapital</h2>
            <p style="text-align: center; color: #6b7080; font-size: 0.9rem;">Código de verificación</p>
            <div style="background: #161921; border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 1.5rem; text-align: center; margin: 1.5rem 0;">
                <div style="font-size: 2.5rem; font-weight: 800; letter-spacing: 0.5rem; color: #3b7dff;">{code}</div>
            </div>
            <p style="color: #6b7080; font-size: 0.85rem; text-align: center;">Este código expira en 10 minutos.</p>
            <p style="color: #6b7080; font-size: 0.75rem; text-align: center; margin-top: 2rem;">Si no solicitaste este código, ignorá este email.</p>
        </div>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False
    
def send_weekly_summary(to_email: str, username: str, portfolio_data: dict):
    """Envía el resumen semanal del portfolio"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📊 Tu resumen semanal - RosKapital'
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = to_email

        positions_html = ""
        for pos in portfolio_data.get("positions", []):
            color = "#089981" if pos.get("rendimiento", 0) >= 0 else "#f23645"
            sign = "+" if pos.get("rendimiento", 0) >= 0 else ""
            positions_html += f"""
            <tr>
                <td style="padding:10px 16px; border-bottom:1px solid #1e222d; color:#e8eaed; font-weight:700; font-size:0.95rem;">{pos['ticker']}</td>
                <td style="padding:10px 16px; border-bottom:1px solid #1e222d; color:#e8eaed; text-align:right; font-size:0.95rem;">${pos['precio_actual']:,.2f}</td>
                <td style="padding:10px 16px; border-bottom:1px solid #1e222d; color:{color}; text-align:right; font-weight:700; font-size:0.95rem;">{sign}{pos.get('rendimiento', 0):.2f}%</td>
            </tr>
            """

        pnl = portfolio_data.get("pnl", 0)
        pnl_pct = portfolio_data.get("pnl_pct", 0)
        pnl_color = "#089981" if pnl >= 0 else "#f23645"
        pnl_sign = "+" if pnl >= 0 else ""
        equity = portfolio_data.get("equity", 100000)
        num_positions = len(portfolio_data.get("positions", []))

        html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 520px; margin: 0 auto; background: #0a0b0f; color: #e8eaed; border-radius: 16px; overflow:hidden;">
            
            <div style="background: linear-gradient(135deg, #0f1117, #161921); padding: 2rem 2rem 1.5rem; text-align:center; border-bottom:1px solid #1e222d;">
                <h2 style="margin:0 0 0.2rem; font-size:1.3rem; font-weight:800; color:#e8eaed;">📊 RosKapital</h2>
                <p style="color:#555; font-size:0.8rem; margin:0;">Resumen semanal</p>
            </div>

            <div style="padding: 1.8rem 2rem;">

                <p style="color:#787b86; font-size:0.85rem; margin:0 0 1.5rem;">Hola <strong style="color:#e8eaed;">{username}</strong>, este es el estado de tu portfolio:</p>
                
                <table style="width:100%; border-collapse:collapse; margin-bottom:1.5rem;">
                    <tr>
                        <td style="padding:1rem; background:#161921; border-radius:10px 0 0 10px; text-align:center; width:50%;">
                            <div style="color:#787b86; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem;">Patrimonio Total</div>
                            <div style="font-size:1.5rem; font-weight:800; color:#e8eaed;">${equity:,.2f}</div>
                            <div style="font-size:0.75rem; color:#787b86; margin-top:0.2rem;">{num_positions} posiciones</div>
                        </td>
                        <td style="padding:1rem; background:#161921; border-radius:0 10px 10px 0; text-align:center; width:50%; border-left:1px solid #0a0b0f;">
                            <div style="color:#787b86; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem;">Rendimiento</div>
                            <div style="font-size:1.5rem; font-weight:800; color:{pnl_color};">{pnl_sign}${abs(pnl):,.2f}</div>
                            <div style="font-size:0.75rem; color:{pnl_color}; margin-top:0.2rem;">{pnl_sign}{pnl_pct:.2f}%</div>
                        </td>
                    </tr>
                </table>

                <table style="width:100%; border-collapse:collapse; background:#161921; border-radius:10px; overflow:hidden;">
                    <thead>
                        <tr style="background:#1a1d28;">
                            <th style="padding:10px 16px; color:#555; font-size:0.7rem; text-align:left; text-transform:uppercase; letter-spacing:0.05em;">Ticker</th>
                            <th style="padding:10px 16px; color:#555; font-size:0.7rem; text-align:right; text-transform:uppercase; letter-spacing:0.05em;">Precio</th>
                            <th style="padding:10px 16px; color:#555; font-size:0.7rem; text-align:right; text-transform:uppercase; letter-spacing:0.05em;">Rend.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {positions_html if positions_html else '<tr><td colspan="3" style="padding:16px; color:#555; text-align:center; font-size:0.85rem;">Sin posiciones abiertas</td></tr>'}
                    </tbody>
                </table>

                <div style="text-align:center; margin-top:2rem;">
                    <a href="http://127.0.0.1:8000/simulador" style="background:linear-gradient(135deg, #3b7dff, #2855cc); color:white; text-decoration:none; padding:0.75rem 2.5rem; border-radius:10px; font-weight:700; font-size:0.85rem; display:inline-block;">
                        Ver portfolio completo
                    </a>
                </div>

            </div>

            <div style="padding:1rem 2rem; border-top:1px solid #1e222d; text-align:center;">
                <p style="color:#444; font-size:0.7rem; margin:0;">RosKapital es una herramienta educativa. No constituye asesoramiento financiero.</p>
            </div>
        </div>
        """

        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando resumen semanal: {e}")
        return False
