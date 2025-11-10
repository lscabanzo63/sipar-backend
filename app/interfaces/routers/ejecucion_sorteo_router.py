from sqlalchemy import func
from app.core.security.deps import roles_required
from app.domain.Exeptions.exceptions import AppException
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.service.sorteo_service import SorteoService
from app.application.common.use_case.schemas.ejecucion_sorteo_schema import EjecutarSorteoRequest, EjecutarSorteoResponse, ResultadoSorteoResponse
from app.infrastructure.db.database import get_db

router = APIRouter(
    prefix="/api/v1/sorteos",
    tags=["sorteos"],
    dependencies=[Depends(roles_required("administrador", "gestor"))],  # <-- guard
)

@router.post("/ejecutar", status_code=status.HTTP_201_CREATED)
def ejecutar_sorteo(request: EjecutarSorteoRequest, db: Session = Depends(get_db)):
    service = SorteoService(db)
    return service.ejecutar_sorteo(request)

""""
@router.get("/resultados", response_model=List[ResultadoSorteoResponse])
def get_resultados(id_conjunto: int, marcar_visto: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = SorteoService(db)
    return service.get_resultados(id_conjunto, marcar_visto)
    """