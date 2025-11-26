from app.core.security.passwords import verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.model import (
    Usuario,
    TipoUsuario,
    Apartamento,
    ConjuntoResidencial,
)
from app.core.security.jwt_service import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    contrasena: str


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Buscar usuario por email
    stmt = (
        select(Usuario)
        .join(TipoUsuario, Usuario.tipo_usuario_id == TipoUsuario.id_tipo_usuario)
        .where(Usuario.email == request.email)
    )
    user: Usuario | None = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    # Validar estado del usuario (bloqueado / inactivo)
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra bloqueado",
        )

    # Validar contraseña
    if not verify_password(request.contrasena, user.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    # Tipo de usuario / rol
    tipo_usuario_nombre = (
        user.tipo_usuario.nombre_tipo_usuario if user.tipo_usuario else "SIN_ROL"
    )

    first_time_flag = bool(user.first_time)

    if user.first_time:
        user.first_time = False
        db.commit()  

    conjunto_id = None
    conjunto_nombre = None

    apto = (
        db.execute(
            select(Apartamento).where(Apartamento.usuario_id == user.id_usuario)
        )
        .scalars()
        .first()
    )

    if apto and apto.conjunto_residencial:
        conjunto_id = apto.conjunto_residencial.id_conjunto_residencial
        conjunto_nombre = apto.conjunto_residencial.nombre_conjunto

    # Crear token JWT
    token = create_access_token(
        subject=user.email,
        role=tipo_usuario_nombre,
        extra={"user_id": user.id_usuario},
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_usuario": user.id_usuario,
            "email": user.email,
            "nombre_completo": f"{user.nombre} {user.apellidos}",
            "rol": tipo_usuario_nombre,
            "tipo_usuario": tipo_usuario_nombre,
            "conjunto_id": conjunto_id,
            "conjunto_nombre": conjunto_nombre,
            "first_time": first_time_flag,  
        },
    }
