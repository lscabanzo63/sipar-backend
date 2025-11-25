from contextlib import contextmanager
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import Date, and_, func, desc
from app.application.common.use_case.schemas.ejecucion_sorteo_schema import GanadorResumen
from app.domain.Exeptions.exceptions import AppException
from app.infrastructure.db.models.model import (
    Sorteo, SorteoFecha, SorteoNorma, Norma,
    ResultadoSorteo, ResultadoSorteoDetalle,
    ConjuntoResidencial, Apartamento, Usuario, TipoUsuario
)
from dateutil.relativedelta import relativedelta
from typing import List, Tuple
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

    def _get_intervalo_por_periodicidad(self, periodicidad: str) -> relativedelta:
        intervalos = {
            'TRIMESTRAL': relativedelta(months=3),
            'CUATRIMESTRAL': relativedelta(months=4),
            'SEMESTRAL': relativedelta(months=6),
        }
        # Si llega algo raro, por defecto 3 meses
        return intervalos.get(periodicidad, relativedelta(months=3))

    def contar_ganadas_en_periodo(
        self,
        usuario_id: int,
        sorteo_id: int,
        fecha_referencia: datetime,
        periodicidad: str,
    ) -> int:
        intervalo = self._get_intervalo_por_periodicidad(periodicidad)
        fecha_inicio_periodo = fecha_referencia - intervalo

        query = (
            self.db.query(func.count(ResultadoSorteoDetalle.id_resultado_sorteo_detalle))
            .join(
                ResultadoSorteo,
                ResultadoSorteoDetalle.resultado_sorteo_id == ResultadoSorteo.id_resultado_sorteo,
            )
            .join(
                SorteoFecha,
                ResultadoSorteo.sorteo_fecha_id == SorteoFecha.id_sorteo_fecha,
            )
            .filter(ResultadoSorteo.sorteo_id == sorteo_id)
            .filter(ResultadoSorteoDetalle.usuario_id == usuario_id)
            .filter(
                and_(
                    SorteoFecha.fecha >= fecha_inicio_periodo,
                    SorteoFecha.fecha <= fecha_referencia,
                )
            )
        )

        total_ganadas = query.scalar() or 0
        return total_ganadas

    def get_normas_activas(self, sorteo_id: int) -> List[Norma]:
        # Puedes añadir filtro de activa aquí si tu modelo lo tiene
        return (
            self.db.query(Norma)
            .join(SorteoNorma)
            .filter(SorteoNorma.sorteo_id == sorteo_id)
            .all()
        )

    def get_n_max_ganadas(self, sorteo_id: int) -> int | None:
        """
        Obtiene el valor de 'n' para la norma ROTACION del sorteo.
        Lee el campo SorteoNorma.parametro (TEXT, normalmente JSON).
        """
        row = (
            self.db.query(SorteoNorma)
            .join(Norma, SorteoNorma.norma_id == Norma.id_norma)
            .filter(SorteoNorma.sorteo_id == sorteo_id)
            .filter(Norma.nombre_norma == "ROTACION")
            .first()
        )

        if not row or not row.parametro:
            return None

        try:
            data = json.loads(row.parametro)
        except Exception:
            # Si el texto es "3" o algo no JSON estándar
            try:
                return int(row.parametro)
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

        # Si nada funcionó, devolvemos None
        return None

    # ========= DATOS BASE =========

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
        """
        Obtiene un usuario por su ID
        Returns: Usuario object or None
        """
        return (
            self.db.query(Usuario)
            .filter(Usuario.id_usuario == usuario_id)
            .first()
        )

    # ========= APLICACIÓN DE REGLAS =========

    def aplicar_rotacion(
        self,
        usuarios: List[Usuario],
        n_max_ganadas: int,
        sorteo_id: int,
        fecha_referencia: datetime,
        periodicidad: str,
    ) -> List[Usuario]:
        """
        Versión simplificada:
        - Un usuario puede ganar como máximo `n_max_ganadas` veces
          en TODO el sorteo (todas las fechas).
        - Si ya alcanzó ese límite, se excluye.
        """
        if n_max_ganadas is None:
            return usuarios

        usuarios_filtrados: List[Usuario] = []

        for u in usuarios:
            total_ganadas = self.contar_ganadas_total(
                usuario_id=u.id_usuario,
                sorteo_id=sorteo_id,
            )

            # print(f"[ROTACION] usuario {u.id_usuario} ha ganado {total_ganadas} veces")

            if total_ganadas < n_max_ganadas:
                usuarios_filtrados.append(u)

        return usuarios_filtrados

    def aplicar_pago_administracion(self, usuarios: List[Usuario]) -> List[Usuario]:
        # Solo usuarios que tienen administracion==True
        return [u for u in usuarios if u.administracion]

    def aplicar_prioridad_propietario(self, usuarios: List[Usuario]) -> List[Usuario]:
        # Propietarios primero (asumiendo tipo_usuario_id == 1)
        return sorted(usuarios, key=lambda u: u.tipo_usuario_id != 1)

    # ========= ASIGNACIÓN / PERSISTENCIA =========

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

    def update_apartamentos_parqueaderos(self, ganadores: List[Tuple[int, int]]):
        for uid, park in ganadores:
            apto = self.db.query(Apartamento).filter(Apartamento.usuario_id == uid).first()
            if apto:
                apto.numero_parqueadero = park
        self.db.commit()

    def marcar_fecha_ejecutada(self, sorteo_fecha_id: int):
        fecha = (
            self.db.query(SorteoFecha)
            .filter(SorteoFecha.id_sorteo_fecha == sorteo_fecha_id)
            .first()
        )
        if fecha:
            fecha.estado = True
            self.db.commit()

    def get_resultados(self, id_conjunto: int, marcar_visto: bool = False) -> List[ResultadoSorteo]:
        sorteo = self.get_sorteo_by_conjunto(id_conjunto)
        if not sorteo:
            return []
        resultados = (
            self.db.query(ResultadoSorteo)
            .filter(ResultadoSorteo.sorteo_id == sorteo.id_sorteo)
            .all()
        )
        if marcar_visto:
            for res in resultados:
                if not res.estado:
                    res.estado = True
            self.db.commit()
        return resultados

    def get_ganadores_resumen(self, resultado_id: int) -> List[GanadorResumen]:
        detalles = (
            self.db.query(ResultadoSorteoDetalle)
            .filter(ResultadoSorteoDetalle.resultado_sorteo_id == resultado_id)
            .all()
        )
        summaries: List[GanadorResumen] = []
        for det in detalles:
            user = (
                self.db.query(Usuario)
                .filter(Usuario.id_usuario == det.usuario_id)
                .first()
            )
            summaries.append(
                GanadorResumen(
                    usuario_id=det.usuario_id,
                    nombre=f"{user.nombre} {user.apellidos}",
                    numero_parqueadero=det.numero_parqueadero,
                )
            )
        return summaries

    def contar_ganadas_total(
        self,
        usuario_id: int,
        sorteo_id: int,
    ) -> int:
        """
        Cuenta cuántas veces ha ganado un usuario en TODO el sorteo
        (sin importar la fecha).
        """
        query = (
            self.db.query(func.count(ResultadoSorteoDetalle.id_resultado_sorteo_detalle))
            .join(
                ResultadoSorteo,
                ResultadoSorteoDetalle.resultado_sorteo_id == ResultadoSorteo.id_resultado_sorteo,
            )
            .filter(ResultadoSorteo.sorteo_id == sorteo_id)
            .filter(ResultadoSorteoDetalle.usuario_id == usuario_id)
        )

        total_ganadas = query.scalar() or 0
        return total_ganadas
