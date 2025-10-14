# app/interfaces/routers/sorteo_router.py
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from app.application.common.use_case.schemas.schema_sorteo import ConfigIn, ConfigOut, ReglaOut
from app.infrastructure.db.dependencies import get_repo
from app.infrastructure.repositories.sorteo_repository import SorteoRepo
from app.application.common.use_case.sorteo_usecase import CreateSorteoConfig
from app.domain.Exeptions.exceptions import DomainError

router = APIRouter(prefix="/api/v1/conjuntos", tags=["sorteos"])

@router.post(
    "/{id_conjunto}/sorteos/configuracion",
    response_model=ConfigOut,
    status_code=201,
    summary="Crear Config",
    description="Crea la configuración del sorteo (periodicidad, fecha de inicio y normas)."
)
def crear_config(
    id_conjunto: int = Path(..., ge=1),
    body: ConfigIn = Body(...)
    ,
    repo: SorteoRepo = Depends(get_repo)
):
    try:
        sid, fechas = CreateSorteoConfig(repo)(
            conjunto_id=id_conjunto,
            periodicidad=body.periodicidad.value,
            fecha_inicio=body.fecha_inicio.isoformat(),
            normas=[n.model_dump() for n in body.normas]
        )

        # construir reglas_asignadas para la salida
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
            fechas_programadas=fechas,
            reglas_asignadas=reglas
        )

    except DomainError as e:
        # Si no tienes un handler global
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
