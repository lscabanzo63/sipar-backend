import unicodedata
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import and_, func
from typing import Any, Dict, List, Tuple

from app.application.common.use_case.schemas.ejecucion_sorteo_schema import GanadorResumen
from app.domain.Exeptions.exceptions import AppException
from app.infrastructure.db.models.model import (
    Sorteo, SorteoFecha, SorteoNorma, Norma,
    ResultadoSorteo, ResultadoSorteoDetalle,
    ConjuntoResidencial, Apartamento, Usuario
)
from fastapi import status
import random
import json


class EjecucionSorteoRepository:
    
    def __init__(self, db: Session):
        self.db = db

    @contextmanager
    def safe_session(self):
        """Context manager for safe database operations"""
        try:
            yield
            self.db.commit()
        except OperationalError as e:
            self.db.rollback()
            raise AppException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error de conexión con la base de datos",
                code="ERR_DB_CONNECTION"
            ) from e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en la base de datos",
                code="ERR_DB_ERROR"
            ) from e

    # ========== BÁSICOS ==========

    def get_sorteo_by_conjunto(self, id_conjunto: int) -> Sorteo:
        try:
            with self.safe_session():
                sorteo = self.db.query(Sorteo).filter(
                    Sorteo.conjunto_residencial_id == id_conjunto
                ).first()
                
                if not sorteo:
                    raise AppException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No se encontró sorteo para el conjunto {id_conjunto}",
                        code="ERR_SORTEO_NOT_FOUND"
                    )
                return sorteo
        except Exception as e:
            if isinstance(e, AppException):
                raise
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo el sorteo",
                code="ERR_GET_SORTEO"
            ) from e
        
    def get_proxima_fecha_disponible(self, sorteo_id: int, fecha_actual: datetime) -> SorteoFecha:
        try:
            # 1. Intentar la fecha exacta que envía el cliente
            fecha_solicitada = self.db.query(SorteoFecha).filter(
                SorteoFecha.sorteo_id == sorteo_id,
                SorteoFecha.fecha == fecha_actual
            ).first()

            if fecha_solicitada:
                if fecha_solicitada.estado:
                    raise AppException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El sorteo para la fecha {fecha_actual.strftime('%Y-%m-%d')} ya fue ejecutado",
                        code="ERR_FECHA_YA_EJECUTADA"
                    )
                return fecha_solicitada

            # 2. Si no existe esa fecha exacta, buscar la próxima no ejecutada >= fecha_actual
            fecha_siguiente = (
                self.db.query(SorteoFecha)
                .filter(
                    SorteoFecha.sorteo_id == sorteo_id,
                    SorteoFecha.fecha >= fecha_actual,
                    SorteoFecha.estado == False
                )
                .order_by(SorteoFecha.fecha.asc())
                .first()
            )

            if not fecha_siguiente:
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hay fechas disponibles para ejecutar el sorteo a partir de {fecha_actual.strftime('%Y-%m-%d')}",
                    code="ERR_NO_FECHA_DISPONIBLE"
                )

            return fecha_siguiente

        except Exception as e:
            if isinstance(e, AppException):
                raise
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo la fecha del sorteo",
                code="ERR_GET_FECHA"
            ) from e

    # ========== NORMAS ==========

    def _normalize_norma_name(self, name: str) -> str:
        """
        Normaliza el nombre de la norma:
        - Quita tildes
        - Pasa a mayúsculas
        Ej: "ROTACIÓN" -> "ROTACION"
        """
        if not name:
            return ""
        nfkd = unicodedata.normalize("NFKD", name)
        sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
        return sin_tildes.upper()

    def get_normas_config(self, sorteo_id: int) -> Dict[str, Dict[str, Any]]:
        rows = (
            self.db.query(Norma, SorteoNorma)
            .join(SorteoNorma, SorteoNorma.norma_id == Norma.id_norma)
            .filter(SorteoNorma.sorteo_id == sorteo_id)
            .all()
        )

        config: Dict[str, Dict[str, Any]] = {}

        for norma, sorteo_norma in rows:
            key = self._normalize_norma_name(norma.nombre_norma)
            config[key] = {
                # sorteo_norma solo tiene sorteo_id, norma_id, parametro
                # así que asumimos "activa" = True mientras exista el registro
                "activa": True,
                "parametro": sorteo_norma.parametro,
            }

        print("[DEBUG] Normas normalizadas:", config)
        return config

    def get_n_max_ganadas(self, sorteo_id: int) -> int | None:
        """
        Obtiene el valor de 'n' para la norma ROTACION del sorteo.
        Lee el campo SorteoNorma.parametro (TEXT, normalmente JSON o un simple número).
        """
        rows = (
            self.db.query(SorteoNorma, Norma)
            .join(Norma, SorteoNorma.norma_id == Norma.id_norma)
            .filter(SorteoNorma.sorteo_id == sorteo_id)
            .all()
        )

        target_key = "ROTACION"
        row_found: SorteoNorma | None = None

        for sorteo_norma, norma in rows:
            nombre_norma_norm = self._normalize_norma_name(norma.nombre_norma)
            if nombre_norma_norm == target_key:
                row_found = sorteo_norma
                break

        if not row_found or not row_found.parametro:
            return None

        raw_param = row_found.parametro

        try:
            data = json.loads(raw_param)
        except Exception:
            # Si el texto es "3" o algo no JSON estándar
            try:
                return int(raw_param)
            except Exception:
                return None

        # Caso 1: parametro es un número directo: 3
        if isinstance(data, (int, float)):
            return int(data)

        # Caso 2: parametro es un dict
        if isinstance(data, dict):
            # Formato: {"parametros": {"n": 3}}
            if "parametros" in data and isinstance(data["parametros"], dict):
                n_val = data["parametros"].get("n")
                if n_val is not None:
                    try:
                        return int(n_val)
                    except Exception:
                        pass

            # Formato: {"n": 3}
            if "n" in data:
                try:
                    return int(data.get("n"))
                except Exception:
                    pass

            # Por si vino con otra key tipo "N" o similar
            for k, v in data.items():
                if str(k).lower() == "n":
                    try:
                        return int(v)
                    except Exception:
                        pass

        return None

    # ========== DATOS BASE ==========

    def get_num_parqueaderos(self, id_conjunto: int) -> int:
        conjunto = (
            self.db.query(ConjuntoResidencial)
            .filter(ConjuntoResidencial.id_conjunto_residencial == id_conjunto)
            .first()
        )
        return conjunto.numero_parqueaderos if conjunto else 0

    def get_usuarios_conjunto(self, id_conjunto: int) -> List[Usuario]:
        return (
            self.db.query(Usuario)
            .join(Apartamento)
            .filter(Apartamento.conjunto_residencial_id == id_conjunto)
            .all()
        )
    
    def get_usuario(self, usuario_id: int) -> Usuario:
        return (
            self.db.query(Usuario)
            .filter(Usuario.id_usuario == usuario_id)
            .first()
        )

    # ========== ROTACIÓN ==========

    def get_ultimas_fechas_ids(
        self,
        sorteo_id: int,
        fecha_referencia: datetime,
        n_periodos: int,
    ) -> list[int]:
        """
        Devuelve los IDs de las últimas `n_periodos` fechas de sorteo
        ANTES de `fecha_referencia` para el sorteo dado.
        """
        if n_periodos <= 0:
            return []

        rows = (
            self.db.query(SorteoFecha.id_sorteo_fecha)
            .filter(SorteoFecha.sorteo_id == sorteo_id)
            .filter(SorteoFecha.fecha < fecha_referencia)
            .order_by(SorteoFecha.fecha.desc())
            .limit(n_periodos)
            .all()
        )

        return [r.id_sorteo_fecha for r in rows]

    def get_usuarios_bloqueados_rotacion(
        self,
        sorteo_id: int,
        fecha_referencia: datetime,
        n_periodos: int,
    ) -> set[int]:
        """
        Devuelve los usuario_id que GANARON en los últimos `n_periodos`
        sorteos ANTES de `fecha_referencia`.
        """
        fechas_ids = self.get_ultimas_fechas_ids(
            sorteo_id=sorteo_id,
            fecha_referencia=fecha_referencia,
            n_periodos=n_periodos,
        )

        if not fechas_ids:
            return set()

        rows = (
            self.db.query(ResultadoSorteoDetalle.usuario_id)
            .join(
                ResultadoSorteo,
                ResultadoSorteoDetalle.resultado_sorteo_id == ResultadoSorteo.id_resultado_sorteo,
            )
            .filter(ResultadoSorteo.sorteo_id == sorteo_id)
            .filter(ResultadoSorteo.sorteo_fecha_id.in_(fechas_ids))
            .distinct()
            .all()
        )

        bloqueados = {r.usuario_id for r in rows}
        print("[ROTACION] Bloqueando usuarios:", bloqueados)
        return bloqueados

    def aplicar_rotacion(
        self,
        usuarios: List[Usuario],
        n_periodos_bloqueo: int,
        sorteo_id: int,
        fecha_referencia: datetime,
        periodicidad: str,  # no lo usamos aquí, pero lo dejamos por compatibilidad
    ) -> List[Usuario]:
        """
        Rotación basada en las últimas N fechas del sorteo:

        - n_periodos_bloqueo = 1 → bloqueo ganadores del último sorteo.
        - n_periodos_bloqueo = 2 → bloqueo ganadores de los últimos 2 sorteos, etc.
        """
        if not n_periodos_bloqueo or n_periodos_bloqueo <= 0:
            return usuarios

        usuarios_bloqueados = self.get_usuarios_bloqueados_rotacion(
            sorteo_id=sorteo_id,
            fecha_referencia=fecha_referencia,
            n_periodos=n_periodos_bloqueo,
        )

        if not usuarios_bloqueados:
            return usuarios

        filtrados = [u for u in usuarios if u.id_usuario not in usuarios_bloqueados]
        print(f"[ROTACION] Usuarios antes: {len(usuarios)}, después: {len(filtrados)}")
        return filtrados

    # ========== OTRAS REGLAS ==========

    def aplicar_pago_administracion(self, usuarios: List[Usuario]) -> List[Usuario]:
        return [u for u in usuarios if u.administracion]

    def aplicar_prioridad_propietario(self, usuarios: List[Usuario]) -> List[Usuario]:
        # Propietarios primero (asumiendo tipo_usuario_id == 1)
        return sorted(usuarios, key=lambda u: u.tipo_usuario_id != 1)

    # ========== ASIGNACIÓN / PERSISTENCIA ==========

    def asignar_parqueaderos(self, usuarios: List[Usuario], id_conjunto: int) -> List[Tuple[int, int]]:
        """
        Asigna parqueaderos aleatoriamente a los usuarios elegibles
        Returns: Lista de tuplas (usuario_id, numero_parqueadero)
        """
        try:
            conjunto = (
                self.db.query(ConjuntoResidencial)
                .filter(ConjuntoResidencial.id_conjunto_residencial == id_conjunto)
                .first()
            )
            
            if not conjunto:
                raise Exception("Conjunto no encontrado")

            num_parqueaderos = conjunto.numero_parqueaderos
            
            parqueaderos_disponibles = list(range(1, num_parqueaderos + 1))
            random.shuffle(parqueaderos_disponibles)
            
            ganadores: List[Tuple[int, int]] = []
            for usuario in usuarios[:num_parqueaderos]:
                if parqueaderos_disponibles:
                    parqueadero = parqueaderos_disponibles.pop(0)
                    ganadores.append((usuario.id_usuario, parqueadero))
                    
                    apartamento = (
                        self.db.query(Apartamento)
                        .filter(
                            Apartamento.usuario_id == usuario.id_usuario,
                            Apartamento.conjunto_residencial_id == id_conjunto,
                        )
                        .first()
                    )
                    
                    if apartamento:
                        apartamento.numero_parqueadero = parqueadero
            
            self.db.commit()
            return ganadores
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error asignando parqueaderos: {str(e)}")
        

    def create_resultado_sorteo(self, sorteo_id: int, fecha_id: int) -> ResultadoSorteo:
        try:
            resultado = ResultadoSorteo(
                sorteo_id=sorteo_id,
                sorteo_fecha_id=fecha_id,
                estado=True,
            )
            self.db.add(resultado)
            self.db.flush()  # Para obtener el id generado
            return resultado
        except Exception as e:
            self.db.rollback()
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creando resultado del sorteo",
                code="ERR_CREATE_RESULTADO"
            ) from e

    def create_detalles(self, resultado_id: int, ganadores: List[Tuple[int, int]]) -> None:
        try:
            for usuario_id, parqueadero in ganadores:
                detalle = ResultadoSorteoDetalle(
                    resultado_sorteo_id=resultado_id,
                    usuario_id=usuario_id,
                    numero_parqueadero=parqueadero,
                )
                self.db.add(detalle)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error guardando detalles del sorteo",
                code="ERR_CREATE_DETALLES"
            ) from e

    # (get_resultados / get_ganadores_resumen puedes dejarlos igual si los usas)
