from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete
from app.infrastructure.db.models.model import (
    ConjuntoResidencial, Ciudad, Usuario, Apartamento
)

class SetupRepository:
    def __init__(self, db: Session):
        self.db = db

    def conjunto_exists(self, id_conjunto: int) -> bool:
        stmt = (
            select(ConjuntoResidencial.id_conjunto_residencial)
            .where(ConjuntoResidencial.id_conjunto_residencial == id_conjunto)
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first() is not None

    def get_conjunto(self, id_conjunto: int) -> Optional[ConjuntoResidencial]:
        return self.db.get(ConjuntoResidencial, id_conjunto)

    def get_usuario(self, id_usuario: int) -> Optional[Usuario]:
        return self.db.get(Usuario, id_usuario)

    def user_associated_with_conjunto(self, id_usuario: int, id_conjunto: int) -> bool:
        stmt = (
            select(Apartamento.id_apartamento)
            .where(
                Apartamento.usuario_id == id_usuario,
                Apartamento.conjunto_residencial_id == id_conjunto
            )
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first() is not None
    
    def fetch_initial(self, id_conjunto: int, id_usuario: int):
        usr = self.db.get(Usuario, id_usuario)

        cjto = self.db.get(ConjuntoResidencial, id_conjunto)

        ciudad_nombre: Optional[str] = None
        if cjto and cjto.ciudad_id:
            ciudad = self.db.get(Ciudad, cjto.ciudad_id)
            ciudad_nombre = ciudad.nombre_ciudad if ciudad else None

        cantidad_parqueaderos = cjto.numero_parqueaderos if cjto and cjto.numero_parqueaderos is not None else 0

        return usr, cjto, ciudad_nombre, cantidad_parqueaderos

    def update_initial(
        self,
        *,
        id_conjunto: int,
        email: Optional[str],
        nombre_conjunto: str,
        ciudad: str,
        direccion: Optional[str],
        telefono: Optional[str],
        cantidad_parqueaderos: int,
    ) -> int:
        
        cjto = self.db.get(ConjuntoResidencial, id_conjunto)
        if not cjto:
            return 404
        
        ciudad_row = self.db.scalar(
            select(Ciudad).where(Ciudad.nombre_ciudad == ciudad).limit(1)
        )
        if not ciudad_row:
            return 404

        ciudad_id = ciudad_row.id_ciudad

        asignados = self.db.scalar(
            select(func.count(func.distinct(Apartamento.numero_parqueadero)))
            .where(Apartamento.conjunto_residencial_id == id_conjunto)
            .where(Apartamento.numero_parqueadero.isnot(None))
        ) or 0

        if cantidad_parqueaderos < asignados:
            return 409

        nombre_conjunto = " ".join(nombre_conjunto.split())
        direccion = " ".join(direccion.split()) if direccion else None
        email = email.lower().strip() if email else None
        telefono = telefono.strip() if telefono else None

        cjto.nombre_conjunto = nombre_conjunto
        cjto.direccion_conjunto = direccion
        cjto.ciudad_id = ciudad_id

        cjto.numero_parqueaderos = cantidad_parqueaderos

        cjto.email_contacto = email
        cjto.telefono_contacto = telefono

        self.db.add(cjto)
        self.db.flush()
        return 200
    
 
    def update_numero_torres(self, id_conjunto: int, num_torres: int) -> int:
        res = self.db.execute(
            update(ConjuntoResidencial)
            .where(ConjuntoResidencial.id_conjunto_residencial == id_conjunto)
            .values(numero_torres=num_torres)
            .execution_options(synchronize_session="fetch")
        )
        return res.rowcount or 0

    def update_numero_apartamentos(self, id_conjunto: int, total: int) -> int:
        res = self.db.execute(
            update(ConjuntoResidencial)
            .where(ConjuntoResidencial.id_conjunto_residencial == id_conjunto)
            .values(numero_apartamentos=total)
            .execution_options(synchronize_session="fetch")
        )
        return res.rowcount or 0

    def generar_apartamentos_preservando_asignaciones(
        self,
        id_conjunto: int,
        torres: int,
        pisos_x_torre: int,
        aptos_x_piso: int,
        reset_parqueadero: bool = True,
    ) -> dict:

        # --- helpers internos seguros ---
        def _safe_int(v, default=None):
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        def _key_from(apto):
            torre = (apto.nombre_torre or "").strip()
            piso = _safe_int(getattr(apto, "piso", None), default=None)
            num = _safe_int(getattr(apto, "numero_apartamento", None), default=None)
            if piso is None or num is None:
                return None
            return (torre, piso, num)

        # 1) obtener apartamentos existentes del conjunto
        existentes = self.db.execute(
            select(Apartamento).where(Apartamento.conjunto_residencial_id == id_conjunto)
        ).scalars().all()

        index_existentes = {}
        incompletos = 0
        for a in existentes:
            k = _key_from(a)
            if k is None:
                incompletos += 1
                continue
            index_existentes.setdefault(k, a)

        insertados = 0
        actualizados = 0
        sin_cambios = 0

        # 2) generar nueva malla de torres/pisos/apartamentos
        for i in range(1, torres + 1):
            torre_name = f"Torre {i}"
            for j in range(1, pisos_x_torre + 1):
                for k in range(1, aptos_x_piso + 1):
                    numero_apto = j * 100 + k
                    k_objetivo = (torre_name, j, numero_apto)

                    if k_objetivo in index_existentes:
                        apto = index_existentes[k_objetivo]
                        changed = False

                        if (apto.nombre_torre or "").strip() != torre_name:
                            apto.nombre_torre = torre_name
                            changed = True
                        if _safe_int(apto.piso) != j:
                            apto.piso = j
                            changed = True
                        if _safe_int(apto.numero_apartamento) != numero_apto:
                            apto.numero_apartamento = numero_apto
                            changed = True

                        if reset_parqueadero and getattr(apto, "numero_parqueadero", None) is not None:
                            apto.numero_parqueadero = None
                            changed = True

                        if changed:
                            actualizados += 1
                        else:
                            sin_cambios += 1
                    else:
                        nuevo = Apartamento(
                            conjunto_residencial_id=id_conjunto,
                            nombre_torre=torre_name,
                            piso=j,
                            numero_apartamento=numero_apto,
                            numero_parqueadero=None,
                            usuario_id=None,  # no asigna usuario
                        )
                        self.db.add(nuevo)
                        insertados += 1

        total_planeado = torres * pisos_x_torre * aptos_x_piso

        # 3) actualizar totales del conjunto
        self.update_numero_torres(id_conjunto, torres)
        self.update_numero_apartamentos(id_conjunto, total_planeado)

        self.db.flush()

        return {
            "insertados": insertados,
            "actualizados": actualizados,
            "sin_cambios": sin_cambios,
            "total_planeado": total_planeado,
            "existentes_previos": len(existentes),
            "existentes_incompletos": incompletos,
        }