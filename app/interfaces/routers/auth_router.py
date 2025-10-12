from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.infrastructure.db.session import get_db
from app.application.common.use_case.schemas.auth import (
    FirstTimeRegisterIn, LoginIn, LoginOut,
)
from app.infrastructure.db.repositories.usuario_respository import UsuariosRepository
from app.application.common.use_case.auth_first_time_register import FirstTimeRegisterUseCase
from app.application.common.use_case.schemas.auth_login import AuthLoginUseCase
from app.infrastructure.db.models.model import Usuario , Apartamento

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/first-time", response_model=LoginOut, status_code=status.HTTP_201_CREATED)
def first_time_register(payload: FirstTimeRegisterIn, db: Session = Depends(get_db)):
    try:
        out = FirstTimeRegisterUseCase(UsuariosRepository(db)).execute(payload)
        db.commit()
        return out
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en registro first-time: {type(e)._name_}: {e}")

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.execute(
        select(Usuario).where(Usuario.email == payload.email)
    ).scalar_one_or_none()

    if not user or user.contrasena != payload.contrasena:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciales inválidas")

    conjunto_id = db.execute(
        select(Apartamento.conjunto_residencial_id).where(
            Apartamento.usuario_id == user.id_usuario
        )
    ).scalar_one_or_none()

    return LoginOut(
        id_usuario=user.id_usuario,
        email=user.email,
        nombre_completo=f"{user.nombre} {user.apellidos}",
        first_time=bool(getattr(user, "first_time", False)),
        conjunto_residencial_id=conjunto_id
    )