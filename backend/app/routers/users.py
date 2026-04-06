"""
Router de Users
Endpoints para gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import get_current_user

router = APIRouter()


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obtiene información del usuario actual"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "investor_profile": current_user.investor_profile,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }


@router.put("/profile")
async def update_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza el perfil del usuario"""
    # TODO: Implementar actualización
    return {"message": "Profile updated - En construcción"}