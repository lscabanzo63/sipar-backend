from typing import Dict, List
from app.domain.Exeptions.exceptions import DomainError
from app.infrastructure.repositories.sorteo_repository import SorteoRepo

class GetSorteoConfig:
    def __init__(self, repo: SorteoRepo):
        self.repo = repo

    def __call__(self, conjunto_id: int) -> Dict:
        s = self.repo.obtener_sorteo_por_conjunto(conjunto_id)
        if not s:
            raise DomainError(404, "ERR_SIN_CONFIGURACION",
                              "El conjunto no tiene un sorteo configurado aún.")

        fechas = self.repo.obtener_fechas_sorteo(s["id_sorteo"])
        normas = self.repo.obtener_normas_sorteo(s["id_sorteo"])

        # construir payload homogéneo para el schema de salida
        return {
            "id_sorteo": s["id_sorteo"],
            "conjunto_id": s["conjunto_residencial_id"],
            "periodicidad": s["periodicidad"],
            "sequence_id": s["sequence_id"],
            "fechas_programadas": [f["fecha"] for f in fechas],
            "reglas_asignadas": normas
        }
