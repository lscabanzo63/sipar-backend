from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.db.session import get_db
from app.application.common.use_case.schemas.setup_schemas import (
    SetupInitialOut, SetupInitialUpdateIn, SetupActionResult, TorresConfigIn
)
from app.infrastructure.db.repositories.setup_repository import SetupRepository
from app.application.common.use_case.setup_initial import (
    SetupInitialGetUseCase, SetupInitialUpdateUseCase, ConfigTorresUseCase
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
    
@router.post("/torres")
def configurar_torres(payload: TorresConfigIn, db: Session = Depends(get_db)):
    try:
        uc = ConfigTorresUseCase(SetupRepository(db))
        result = uc.execute(payload)
        db.commit()
        return result
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {type(e).__name__}: {e}")
