from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db
from app.application.common.use_case.schemas.auth import (
    FirstTimeRegisterIn, LoginIn, LoginOut
)
from app.infrastructure.db.repositories.usuario_respository import UsuariosRepository
from app.application.common.use_case.auth_first_time_register import FirstTimeRegisterUseCase
from app.application.common.use_case.schemas.auth_login import AuthLoginUseCase

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/first-time", response_model=LoginOut, status_code=status.HTTP_201_CREATED)
def first_time_register(payload: FirstTimeRegisterIn, db: Session = Depends(get_db)):
    try:
        out = FirstTimeRegisterUseCase(UsuariosRepository(db)).execute(payload)
        db.commit()
        return out  # first_time: true
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        # En desarrollo puedes devolver e para ver el motivo exacto
        raise HTTPException(status_code=500, detail=f"Error en registro first-time: {type(e).__name__}: {e}")

@router.post("/login", response_model=LoginOut, status_code=status.HTTP_200_OK)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    try:
        out = AuthLoginUseCase(UsuariosRepository(db)).execute(payload)
        db.commit()  # si dentro del use case pones disable_first_time
        return out
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=401, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en login: {type(e).__name__}: {e}")
