from datetime import datetime
from app.domain.usuarios.dates import fechas_ciclo          
from app.domain.Exeptions.exceptions import DomainError
        

class CreateSorteoConfig:
    def __init__(self, repo):
        self.repo = repo

    def __call__(self, conjunto_id: int, periodicidad: str, fecha_inicio: str, normas: list):
        # Parse ISO (maneja 'Z' si llegara): "2026-02-01T00:00:00" OK
        try:
            # Si usas 'Z' en el ISO, haz un replace('Z','') o usa dateutil.parser.parse
            dt0 = datetime.fromisoformat(fecha_inicio.replace('Z',''))
        except Exception as e:
            raise DomainError(400, "ERR_FECHA_INVALIDA", f"Formato de fecha_inicio inválido: {e}")

        # Cálculo de fechas
        try:
            fechas = fechas_ciclo(dt0, periodicidad)
        except ValueError as e:
            # periodicidad fuera del dominio
            raise DomainError(400, "ERR_PERIODICIDAD_DESCONOCIDA", str(e))

        # ... aquí tu lógica de persistencia ...
        sid = self.repo.crear_sorteo(conjunto_id, periodicidad)
        self.repo.insertar_fechas(sid, fechas)
        self.repo.insertar_normas(sid, normas)
        self.repo.commit()

        return sid, fechas