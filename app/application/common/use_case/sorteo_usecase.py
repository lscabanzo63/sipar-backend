from datetime import datetime
from app.domain.usuarios.dates import fechas_ciclo
from app.domain.Exeptions.exceptions import DomainError
from app.infrastructure.repositories.sorteo_repository import SorteoRepo

class UpsertSorteoConfig:
    def __init__(self, repo: SorteoRepo):
        self.repo = repo

    def __call__(self, conjunto_id: int, periodicidad: str, fecha_inicio: str, normas: list):
        try:
            dt0 = datetime.fromisoformat(fecha_inicio.replace("Z",""))
        except Exception as e:
            raise DomainError(400, "ERR_FECHA_INVALIDA", f"Formato inválido en fecha_inicio: {e}")

        try:
            fechas = fechas_ciclo(dt0, periodicidad)
        except ValueError:
            raise DomainError(400, "ERR_PERIODICIDAD_DESCONOCIDA",
                              "La periodicidad debe ser TRIMESTRAL, CUATRIMESTRAL o SEMESTRAL.")


        row = self.repo.obtener_sorteo_por_conjunto_for_update(conjunto_id)

        if row is None:
            meta = self.repo.crear_sorteo(conjunto_id, periodicidad)
            sid, sequence_id = meta["id_sorteo"], meta["sequence_id"]
        else:
            # actualizar y subir sequence_id
            sid = row["id_sorteo"]
            sequence_id = self.repo.actualizar_incrementando_sequence(sid, periodicidad)
            # reemplazar fechas / normas
            self.repo.borrar_fechas(sid)
            self.repo.borrar_normas(sid)

        # insertar nuevas fechas y normas
        self.repo.insertar_fechas(sid, fechas)
        self.repo.insertar_normas(sid, normas)

        self.repo.commit()
        return sid, fechas, sequence_id