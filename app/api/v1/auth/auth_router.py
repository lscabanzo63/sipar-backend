from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.model import Usuario, TipoUsuario
from app.core.security.jwt_service import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    contrasena: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    result = db.execute(
        select(Usuario, TipoUsuario.nombre_tipo_usuario)
        .join(TipoUsuario, Usuario.tipo_usuario_id == TipoUsuario.id_tipo_usuario)
        .where(Usuario.email == payload.email)
    ).first()

    if not result:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    user, rol = result
    if user.contrasena != payload.contrasena:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token = create_access_token(
        subject=user.email,
        role=rol,
        extra={"user_id": user.id_usuario}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_usuario": user.id_usuario,
            "email": user.email,
            "nombre_completo": f"{user.nombre} {user.apellidos}",
            "rol": rol
        }
    }
