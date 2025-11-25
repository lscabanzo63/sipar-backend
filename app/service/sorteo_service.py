from datetime import datetime
from app.application.common.use_case.schemas.ejecucion_sorteo_schema import (
    EjecutarSorteoRequest,
    EjecutarSorteoResponse,
    GanadorResumen,
)
from app.domain.Exeptions.exceptions import AppException
from sqlalchemy.orm import Session
from app.infrastructure.repositories.ejecucion_sorteo_repository import EjecucionSorteoRepository
from fastapi import status


class SorteoService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = EjecucionSorteoRepository(db)

    def ejecutar_sorteo(self, request: EjecutarSorteoRequest) -> EjecutarSorteoResponse:
        try:
            # Obtener sorteo configurado
            sorteo = self.repository.get_sorteo_by_conjunto(request.id_conjunto)
            print(f"Sorteo encontrado: {sorteo.id_sorteo if sorteo else 'No encontrado'}")
            
            if not sorteo:
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontró sorteo para el conjunto {request.id_conjunto}",
                    code="ERR_SORTEO_NOT_FOUND"
                )
    
            # Validar periodicidad
            if sorteo.periodicidad not in ["TRIMESTRAL", "CUATRIMESTRAL", "SEMESTRAL"]:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Periodicidad inválida: {sorteo.periodicidad}. "
                        "Debe ser TRIMESTRAL, CUATRIMESTRAL o SEMESTRAL"
                    ),
                    code="ERR_INVALID_PERIODICITY",
                )
                
            print(f"Sorteo encontrado: {sorteo.id_sorteo}")
            
            # Usar la fecha del request (no datetime.now)
            fecha = self.repository.get_proxima_fecha_disponible(
                sorteo.id_sorteo,
                request.fecha_actual,
            )
            print(f"Fecha próxima: {fecha.fecha if fecha else 'No hay fecha'}")

            if not fecha:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hay fechas disponibles para ejecutar el sorteo",
                    code="ERR_NO_FECHA_DISPONIBLE",
                )

            # ─────────────────────────────────────────────
            # Límite de ganadas según norma ROTACION
            # ─────────────────────────────────────────────
            n_max_ganadas = self.repository.get_n_max_ganadas(sorteo.id_sorteo)

            # Log de depuración para verificar qué se está usando realmente
           # print(f"[ROTACION] n_max_ganadas resuelto desde BD: {n_max_ganadas}")

            # Si no hay norma ROTACION o el JSON está raro, dejamos un valor por defecto
            # Como tú quieres trabajar con 3 cuando no se pueda leer, dejo 3.
            if n_max_ganadas is None:
                n_max_ganadas = 3
               # print(f"[ROTACION] n_max_ganadas usando valor por defecto: {n_max_ganadas}")

            # Obtener usuarios del conjunto
            usuarios = self.repository.get_usuarios_conjunto(request.id_conjunto)
            if not usuarios:
                raise AppException(
                    status_code=400,
                    detail="No hay usuarios para sortear",
                    code="ERR_NO_USERS",
                )

            # Aplicar reglas de negocio
            usuarios = self.repository.aplicar_pago_administracion(usuarios)

            usuarios = self.repository.aplicar_rotacion(
                usuarios=usuarios,
                n_max_ganadas=n_max_ganadas,
                sorteo_id=sorteo.id_sorteo,
                fecha_referencia=fecha.fecha,
                periodicidad=sorteo.periodicidad,
            )

            usuarios = self.repository.aplicar_prioridad_propietario(usuarios)

            if not usuarios:
                raise AppException(
                    status_code=400,
                    detail="No hay usuarios elegibles después de aplicar las reglas",
                    code="ERR_NO_ELIGIBLE_USERS",
                )

            # Crear resultado del sorteo
            resultado = self.repository.create_resultado_sorteo(
                sorteo.id_sorteo,
                fecha.id_sorteo_fecha,
            )
            
            # Asignar parqueaderos
            ganadores = self.repository.asignar_parqueaderos(
                usuarios,
                request.id_conjunto,
            )
            
            # Guardar detalles del resultado
            self.repository.create_detalles(
                resultado.id_resultado_sorteo,
                ganadores,
            )

            # Marcar fecha como ejecutada
            fecha.estado = True
            self.db.commit()

            # Preparar respuesta
            ganadores_response = []
            for uid, park in ganadores:
                if park is not None:
                    usuario = self.repository.get_usuario(uid)
                    if usuario:
                        ganador = GanadorResumen(
                            usuario_id=uid,
                            nombre=f"{usuario.nombre} {usuario.apellidos}",
                            numero_parqueadero=park,
                        )
                        ganadores_response.append(ganador)

            return EjecutarSorteoResponse(
                id_resultado_sorteo=resultado.id_resultado_sorteo,
                fecha_sorteo=fecha.fecha,
                mensaje="Sorteo ejecutado exitosamente",
                ganadores=ganadores_response,
            )
                        
        except Exception as e:
            self.db.rollback()
            print(f"Error ejecutando sorteo: {str(e)}")
            if isinstance(e, AppException):
                raise
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno ejecutando sorteo",
                code="ERR_INTERNAL_SERVER",
            )
