from psycopg import logger
from app.core.security.deps import roles_required
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.db.database import get_db
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

router = APIRouter(
    prefix="/api/v1/conjuntos",
    tags=["Setup"],
    # ⬇⬇⬇ roles en MAYÚSCULAS para coincidir con el JWT
    dependencies=[Depends(roles_required("administrador", "gestor"))]
)

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
        # Conjunto o recurso no encontrado
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar configuración: {type(e).__name__}: {e}")

@router.patch("/initial", response_model=SetupActionResult, status_code=status.HTTP_200_OK)
def patch_initial_config(payload: SetupInitialUpdateIn, db: Session = Depends(get_db)):
    try:
        uc = SetupInitialUpdateUseCase(SetupRepository(db))
        result = uc.execute(payload)

        # Normaliza a minúsculas por si el caso de uso retorna "OK"/"Ok"/"ok"
        result.status = (result.status or "").lower()

        if result.status == "ok":
            db.commit()
            # 200 OK con el mismo cuerpo del caso de uso
            return result

        # Errores mapeados a códigos HTTP
        db.rollback()

        if result.status == "not_found":
            # 404: conjunto o ciudad no existe (según tu use case)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message or "Recurso no encontrado."
            )

        if result.status == "validation_error":
            # 422: datos inválidos
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.message or "Datos de entrada inválidos."
            )

        if result.status == "conflict":
            # 409: capacidad menor a asignados, duplicado, etc.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result.message or "Conflicto de negocio."
            )

        # Cualquier estado desconocido → 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.message or "Error no controlado."
        )

    except (ValueError,) as e:
        db.rollback()
        # Si tu caso de uso lanza ValueError en validaciones, traducimos a 422
        raise HTTPException(status_code=422, detail=str(e))

    except (NoResultFound,) as e:
        db.rollback()
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")

    except (MultipleResultsFound,) as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Inconsistencia de datos: múltiples registros.")

    except (IntegrityError,) as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflicto de integridad (duplicado o FK).")

    except (SQLAlchemyError,) as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de base de datos.")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error no controlado: {type(e).__name__}")

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
