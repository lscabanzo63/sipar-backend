from contextlib import contextmanager
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import asc, func, desc
from app.application.common.use_case.schemas.ejecucion_sorteo_schema import GanadorResumen
from app.domain.Exeptions.exceptions import AppException
from app.infrastructure.db.models.model import Sorteo, SorteoFecha, SorteoNorma, Norma, ResultadoSorteo, ResultadoSorteoDetalle, ConjuntoResidencial, Apartamento, Usuario, TipoUsuario
from typing import List, Tuple
from fastapi import status
import random

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
        fecha = self.db.query(SorteoFecha).filter(
            SorteoFecha.sorteo_id == sorteo_id,
            SorteoFecha.fecha > fecha_actual,
            SorteoFecha.estado == False
        ).order_by(SorteoFecha.fecha.asc()).first()
        
        if not fecha:
            raise AppException(
                status_code=400,
                detail="No hay fechas disponibles",
                code="ERR_NO_DATES"
            )
        
        return fecha

    def get_normas_activas(self, sorteo_id: int) -> List[Norma]:
        return self.db.query(Norma).join(SorteoNorma).filter(SorteoNorma.sorteo_id == sorteo_id).all()

    def get_num_parqueaderos(self, id_conjunto: int) -> int:
        conjunto = self.db.query(ConjuntoResidencial).filter(ConjuntoResidencial.id_conjunto_residencial == id_conjunto).first()
        return conjunto.numero_parqueaderos if conjunto else 0

    def get_usuarios_conjunto(self, id_conjunto: int) -> List[Usuario]:
        return self.db.query(Usuario).join(Apartamento).filter(Apartamento.conjunto_residencial_id == id_conjunto).all()
    
    def get_usuario(self, usuario_id: int) -> Usuario:
            """
            Obtiene un usuario por su ID
            Returns: Usuario object or None
            """
            return self.db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    
    # Aplicar reglas: funciones separadas por SRP.
    def aplicar_rotacion(self, usuarios: List[Usuario], n: int, sorteo_id: int) -> List[Usuario]:
        # Obtener últimos N resultados para el sorteo.
        ultimos_resultados = self.db.query(ResultadoSorteo).filter(
            ResultadoSorteo.sorteo_id == sorteo_id
        ).order_by(desc(ResultadoSorteo.sorteo_fecha_id)).limit(n).all()
        
        ultimos_fecha_ids = [res.sorteo_fecha_id for res in ultimos_resultados]
        
        # Para cada usuario, check si ganó en TODOS los últimos N.
        excluidos = set()
        if ultimos_fecha_ids:
            ganadores_ultimos = self.db.query(ResultadoSorteoDetalle.usuario_id, func.count()).filter(
                ResultadoSorteoDetalle.resultado_sorteo_id.in_([res.id_resultado_sorteo for res in ultimos_resultados])
            ).group_by(ResultadoSorteoDetalle.usuario_id).having(func.count() == len(ultimos_fecha_ids)).all()
            excluidos = {uid for uid, _ in ganadores_ultimos}
        
        return [u for u in usuarios if u.id_usuario not in excluidos]

    def aplicar_pago_administracion(self, usuarios: List[Usuario]) -> List[Usuario]:
        # Filtrar minoría: no pagados, pero como optimización, query direct.
        return [u for u in usuarios if u.administracion]  # True: pagado

    def aplicar_prioridad_propietario(self, usuarios: List[Usuario]) -> List[Usuario]:
        # Ordenar: propietarios primero (asumir tipo_usuario_id=1 es propietario)
        return sorted(usuarios, key=lambda u: u.tipo_usuario_id != 1)  # False (0) para propietarios primero

    def asignar_parqueaderos(self, usuarios: List[Usuario], id_conjunto: int) -> List[Tuple[int, int]]:
        """
        Asigna parqueaderos aleatoriamente a los usuarios elegibles
        Returns: Lista de tuplas (usuario_id, numero_parqueadero)
        """
        try:
            # Obtener número total de parqueaderos del conjunto
            conjunto = self.db.query(ConjuntoResidencial).filter(
                ConjuntoResidencial.id_conjunto_residencial == id_conjunto
            ).first()
            
            if not conjunto:
                raise Exception("Conjunto no encontrado")

            num_parqueaderos = conjunto.numero_parqueaderos
            
            # Crear lista de parqueaderos disponibles
            parqueaderos_disponibles = list(range(1, num_parqueaderos + 1))
            random.shuffle(parqueaderos_disponibles)
            
            # Asignar parqueaderos
            ganadores = []
            for usuario in usuarios[:num_parqueaderos]:  # Limitar a número de parqueaderos
                if parqueaderos_disponibles:
                    parqueadero = parqueaderos_disponibles.pop(0)
                    ganadores.append((usuario.id_usuario, parqueadero))
                    
                    # Actualizar el número de parqueadero en la tabla apartamento
                    apartamento = self.db.query(Apartamento).filter(
                        Apartamento.usuario_id == usuario.id_usuario,
                        Apartamento.conjunto_residencial_id == id_conjunto
                    ).first()
                    
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
                estado=True
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
        """
        Guarda los detalles del resultado del sorteo
        Args:
            resultado_id: ID del resultado del sorteo
            ganadores: Lista de tuplas (usuario_id, numero_parqueadero)
        """
        try:
            for usuario_id, parqueadero in ganadores:
                detalle = ResultadoSorteoDetalle(
                    resultado_sorteo_id=resultado_id,
                    usuario_id=usuario_id,
                    numero_parqueadero=parqueadero
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
        fecha = self.db.query(SorteoFecha).filter(SorteoFecha.id_sorteo_fecha == sorteo_fecha_id).first()
        if fecha:
            fecha.estado = True
            self.db.commit()

    def get_resultados(self, id_conjunto: int, marcar_visto: bool = False) -> List[ResultadoSorteo]:
        sorteo = self.get_sorteo_by_conjunto(id_conjunto)
        if not sorteo:
            return []
        resultados = self.db.query(ResultadoSorteo).filter(ResultadoSorteo.sorteo_id == sorteo.id_sorteo).all()
        if marcar_visto:
            for res in resultados:
                if not res.estado:
                    res.estado = True
            self.db.commit()
        return resultados

    # Helper para resumen ganadores
    def get_ganadores_resumen(self, resultado_id: int) -> List[GanadorResumen]:
        detalles = self.db.query(ResultadoSorteoDetalle).filter(ResultadoSorteoDetalle.resultado_sorteo_id == resultado_id).all()
        summaries = []
        for det in detalles:
            user = self.db.query(Usuario).filter(Usuario.id_usuario == det.usuario_id).first()
            summaries.append(GanadorResumen(usuario_id=det.usuario_id, nombre=f"{user.nombre} {user.apellidos}", numero_parqueadero=det.numero_parqueadero))
        return summaries