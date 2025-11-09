from sqlalchemy import func
from app.domain.Exeptions.exceptions import AppException
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.service.sorteo_service import SorteoService
from app.application.common.use_case.schemas.ejecucion_sorteo_schema import EjecutarSorteoRequest, EjecutarSorteoResponse, ResultadoSorteoResponse
from app.infrastructure.db.session import get_db
from app.infrastructure.db.models.deps import get_current_user
from app.infrastructure.db.models.model import SorteoFecha, User
from typing import List

router = APIRouter(prefix="/api/v1/sorteos", tags=["sorteos"])

@router.post("/ejecutar", response_model=EjecutarSorteoResponse, status_code=status.HTTP_201_CREATED)
def ejecutar_sorteo(request: EjecutarSorteoRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.rol != "ADMIN":
        raise AppException(status.HTTP_403_FORBIDDEN, "No autorizado", "ERR_NO_ADMIN")
    
    service = SorteoService(db)
    return service.ejecutar_sorteo(request)

@router.get("/resultados", response_model=List[ResultadoSorteoResponse])
def get_resultados(id_conjunto: int, marcar_visto: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = SorteoService(db)
    return service.get_resultados(id_conjunto, marcar_visto)