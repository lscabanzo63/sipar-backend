from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.db.session import get_db

from app.application.common.use_case.schemas.setup import (
    SetupInitialOut, SetupInitialUpdateIn, SetupActionResult
)
from app.infrastructure.db.repositories.setup_repository import SetupRepository
from app.application.common.use_case.setup_initial import (
    SetupInitialGetUseCase, SetupInitialUpdateUseCase
)

router = APIRouter(prefix="/setup", tags=["Setup"])

@router.get("/initial", response_model=SetupInitialOut)
def get_initial_config(
    id_conjunto: int = Query(..., gt=0),
    id_usuario: int = Query(..., gt=0),
    db: Session = Depends(get_db)
):
    try:
        uc = SetupInitialGetUseCase(SetupRepository(db))
        return uc.execute(id_conjunto, id_usuario)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar configuración: {type(e).__name__}: {e}")

@router.patch("/initial", response_model=SetupActionResult, status_code=status.HTTP_200_OK)
def patch_initial_config(payload: SetupInitialUpdateIn, db: Session = Depends(get_db)):
    try:
        uc = SetupInitialUpdateUseCase(SetupRepository(db))
        result = uc.execute(payload)
        # commit solo si guardó (status ok)
        if result.status == "ok":
            db.commit()
        else:
            db.rollback()
        return result
    except Exception as e:
        db.rollback()
        return SetupActionResult(
            status="error",
            message=f"Error al guardar configuración: {type(e).__name__}: {e}"
        )
