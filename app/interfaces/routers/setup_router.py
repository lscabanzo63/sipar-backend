from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.db.session import get_db
from app.application.common.use_case.schemas.setup_schemas import (
    SetupInitialOut, SetupInitialUpdateIn, SetupActionResult, TorresConfigIn
)
from app.infrastructure.repositories.setup_repository import SetupRepository
from app.application.common.use_case.setup_initial import (
    SetupInitialGetUseCase, SetupInitialUpdateUseCase, ConfigTorresUseCase
)
import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

router = APIRouter(prefix="/setup", tags=["Setup"])
logger = logging.getLogger("uvicorn.error")

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

        # Normaliza a minúsculas para evitar confusiones "OK"/"ok"
        result.status = (result.status or "").lower()

        if result.status == "ok":
            db.commit()
        else:
            db.rollback()

        return result

    except (ValueError,) as e:
        db.rollback()
        logger.warning("Validation error in /initial: %s", e)
        return SetupActionResult(
            status="validation_error",
            message=str(e),
        )

    except (NoResultFound,) as e:
        db.rollback()
        logger.info("Not found in /initial: %s", e)
        return SetupActionResult(
            status="not_found",
            message="Recurso no encontrado."
        )

    except (MultipleResultsFound,) as e:
        db.rollback()
        logger.warning("Data inconsistency in /initial: %s", e)
        return SetupActionResult(
            status="conflict",
            message="Inconsistencia de datos: múltiples registros."
        )

    except (IntegrityError,) as e:
        db.rollback()
        logger.error("IntegrityError in /initial: %s", e, exc_info=True)
        return SetupActionResult(
            status="conflict",
            message="Conflicto de integridad (duplicado o FK)."
        )

    except (SQLAlchemyError,) as e:
        db.rollback()
        logger.error("SQLAlchemyError in /initial: %s", e, exc_info=True)
        return SetupActionResult(
            status="error",
            message="Error de base de datos."
        )

    except Exception as e:
        db.rollback()
        logger.exception("Unhandled error in /initial")
        return SetupActionResult(
            status="error",
            message=f"Error no controlado: {type(e).__name__}"
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
