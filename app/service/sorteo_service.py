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
            # 1. Obtener sorteo configurado
            sorteo = self.repository.get_sorteo_by_conjunto(request.id_conjunto)
            print(f"[SORTEO] Sorteo encontrado: {sorteo.id_sorteo if sorteo else 'No encontrado'}")
            
            if not sorteo:
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontró sorteo para el conjunto {request.id_conjunto}",
                    code="ERR_SORTEO_NOT_FOUND"
                )
    
            # 2. Validar periodicidad
            if sorteo.periodicidad not in ["TRIMESTRAL", "CUATRIMESTRAL", "SEMESTRAL"]:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Periodicidad inválida: {sorteo.periodicidad}. "
                        "Debe ser TRIMESTRAL, CUATRIMESTRAL o SEMESTRAL"
                    ),
                    code="ERR_INVALID_PERIODICITY",
                )
                
            print(f"[SORTEO] Periodicidad: {sorteo.periodicidad}")
            
            # 3. Obtener la fecha del sorteo a ejecutar (usa la fecha del request)
            fecha = self.repository.get_proxima_fecha_disponible(
                sorteo.id_sorteo,
                request.fecha_actual,
            )
            print(f"[SORTEO] Fecha próxima a ejecutar: {fecha.fecha if fecha else 'No hay fecha'}")

            if not fecha:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hay fechas disponibles para ejecutar el sorteo",
                    code="ERR_NO_FECHA_DISPONIBLE",
                )

            # 4. Obtener usuarios del conjunto
            usuarios = self.repository.get_usuarios_conjunto(request.id_conjunto)
            print(f"[SORTEO] Usuarios iniciales en conjunto {request.id_conjunto}: {len(usuarios)}")

            if not usuarios:
                raise AppException(
                    status_code=400,
                    detail="No hay usuarios para sortear",
                    code="ERR_NO_USERS",
                )

            # ─────────────────────────────────────────────
            # 5. Leer configuración de normas para este sorteo
            # ─────────────────────────────────────────────
            normas_config = self.repository.get_normas_config(sorteo.id_sorteo)
            print("[SORTEO] Normas configuradas (normalizadas):", normas_config)

            cfg_pago = normas_config.get("PAGO_ADMINISTRACION", {})
            cfg_prioridad = normas_config.get("PRIORIDAD_PROPIETARIO", {})
            cfg_rotacion = normas_config.get("ROTACION", {})

            aplica_pago_admin = cfg_pago.get("activa", False)
            aplica_prioridad_prop = cfg_prioridad.get("activa", False)
            aplica_rotacion = cfg_rotacion.get("activa", False)
            # ─────────────────────────────────────────────
            # 6. Aplicar reglas según configuración
            # ─────────────────────────────────────────────

            # 6.1 PAGO_ADMINISTRACION
            if aplica_pago_admin:
                print("[REGLA] Aplicando PAGO_ADMINISTRACION")
                usuarios = self.repository.aplicar_pago_administracion(usuarios)
                print(f"[REGLA] Usuarios después de PAGO_ADMINISTRACION: {len(usuarios)}")

            # 6.2 ROTACION (últimas N fechas de sorteo)
            if aplica_rotacion:
                print("[REGLA] Aplicando ROTACION")
                # Leer n desde la config de BD (tabla sorteo_norma)
                n_rotacion = self.repository.get_n_max_ganadas(sorteo.id_sorteo)
                # Si no se pudo leer nada del parámetro, asumimos 1
                if not n_rotacion or n_rotacion <= 0:
                    n_rotacion = 1

                print(f"[REGLA] ROTACION activa con n = {n_rotacion}")

                usuarios = self.repository.aplicar_rotacion(
                    usuarios=usuarios,
                    n_periodos_bloqueo=n_rotacion,
                    sorteo_id=sorteo.id_sorteo,
                    fecha_referencia=fecha.fecha,
                    periodicidad=sorteo.periodicidad,  # la firma lo pide, aunque adentro no se use ya
                )
                print(f"[REGLA] Usuarios después de ROTACION: {len(usuarios)}")

            # 6.3 PRIORIDAD_PROPIETARIO
            if aplica_prioridad_prop:
                print("[REGLA] Aplicando PRIORIDAD_PROPIETARIO")
                usuarios = self.repository.aplicar_prioridad_propietario(usuarios)
                print(f"[REGLA] Usuarios después de PRIORIDAD_PROPIETARIO: {len(usuarios)}")

            if not usuarios:
                raise AppException(
                    status_code=400,
                    detail="No hay usuarios elegibles después de aplicar las reglas",
                    code="ERR_NO_ELIGIBLE_USERS",
                )

            # 7. Crear resultado del sorteo
            resultado = self.repository.create_resultado_sorteo(
                sorteo.id_sorteo,
                fecha.id_sorteo_fecha,
            )
            print(f"[SORTEO] Resultado creado con id {resultado.id_resultado_sorteo}")
            
            # 8. Asignar parqueaderos
            ganadores = self.repository.asignar_parqueaderos(
                usuarios,
                request.id_conjunto,
            )
            print(f"[SORTEO] Ganadores asignados: {len(ganadores)}")
            
            # 9. Guardar detalles del resultado
            self.repository.create_detalles(
                resultado.id_resultado_sorteo,
                ganadores,
            )

            # 10. Marcar fecha como ejecutada
            fecha.estado = True
            self.db.commit()
            print("[SORTEO] Fecha marcada como ejecutada")

            # 11. Preparar respuesta
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
            print(f"[SORTEO] Error ejecutando sorteo: {str(e)}")
            if isinstance(e, AppException):
                raise
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno ejecutando sorteo",
                code="ERR_INTERNAL_SERVER",
            )
