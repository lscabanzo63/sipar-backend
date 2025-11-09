# app/interfaces/routers/sorteo_router.py
from app.application.common.use_case.get_sorteo_config_usecase import GetSorteoConfig
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from app.application.common.use_case.schemas.schema_sorteo import ConfigIn, ConfigOut, ReglaOut
from app.infrastructure.db.dependencies import get_repo
from app.infrastructure.repositories.sorteo_repository import SorteoRepo
from app.application.common.use_case.sorteo_usecase import UpsertSorteoConfig
from app.domain.Exeptions.exceptions import DomainError
from app.infrastructure.db.models.deps import get_session  


router = APIRouter(prefix="/api/v1/conjuntos", tags=["sorteos"])

@router.post(
    "/{id_conjunto}/sorteos/configuracion",
    response_model=ConfigOut,
    status_code=201,
    summary="Crear/Actualizar configuración del sorteo (upsert)",
    description="Si no existe sorteo para el conjunto: crea (sequence_id=1). Si existe: actualiza y aumenta sequence_id en 1."
)
def upsert_config(
    id_conjunto: int = Path(..., ge=1),
    body: ConfigIn = Body(...)
    ,
    repo: SorteoRepo = Depends(get_repo)
):
    try:
        sid, fechas, seq = UpsertSorteoConfig(repo)(
            conjunto_id=id_conjunto,
            periodicidad=body.periodicidad.value,
            fecha_inicio=body.fecha_inicio.isoformat(),
            normas=[n.model_dump() for n in body.normas]
        )

        reglas: list[ReglaOut] = []
        for n in body.normas:
            if not n.activa:
                continue
            if n.tipo == n.tipo.ROTACION:
                reglas.append(ReglaOut(tipo=n.tipo, parametros={"n": n.parametros["n"]}))
            else:
                reglas.append(ReglaOut(tipo=n.tipo))

        return ConfigOut(
            id_sorteo=sid,
            conjunto_id=id_conjunto,
            periodicidad=body.periodicidad,
            sequence_id=seq,             
            fechas_programadas=fechas,
            reglas_asignadas=reglas
        )

    except DomainError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
    
def get_sorteo_repo(db: Session = Depends(get_session)) -> SorteoRepo:
    return SorteoRepo(db)  

@router.get(
    "/{id_conjunto}/sorteos/",
    response_model=ConfigOut,
    summary="Obtener configuración de sorteo del conjunto",
)
def obtener_configuracion_sorteo(
    id_conjunto: int = Path(..., ge=1),
    repo: SorteoRepo = Depends(get_sorteo_repo),
):
    try:
        return GetSorteoConfig(repo)(conjunto_id=id_conjunto)
    except DomainError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})