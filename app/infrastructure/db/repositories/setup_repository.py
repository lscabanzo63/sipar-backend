from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
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

    def user_associated_with_conjunto(self, id_usuario: int, id_conjunto: int) -> bool:
    # Versión basada únicamente en apartamento (recomendada dado tu esquema)
        stmt_apto = (
            select(Apartamento.id_apartamento)
            .where(
                Apartamento.usuario_id == id_usuario,
                Apartamento.conjunto_residencial_id == id_conjunto
            )
            .limit(1)
        )
        return self.db.execute(stmt_apto).scalars().first() is not None

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

    def generar_apartamentos(self, id_conjunto: int, torres: int, pisos_x_torre: int, aptos_x_piso: int):
            aptos_to_insert = []

            for j in range(1, pisos_x_torre + 1):          # pisos
                for i in range(1, torres + 1):             # torres
                    for k in range(1, aptos_x_piso + 1):   # aptos por piso
                        # Numeración continua por piso a través de torres, y reinicia por piso
                        sec_en_piso = (i - 1) * aptos_x_piso + k          # 1..(torres*aptos_x_piso)
                        numero_apto = j * 100 + sec_en_piso               # ej: 1*100 + 1 -> 101

                        aptos_to_insert.append({
                            "torre": f"Torre {i}",
                            "numero_apto": numero_apto,   # entero, no string
                            "piso": j
                        })

            # Inserción (mejor flush/commit fuera del bucle)
            for a in aptos_to_insert:
                self.db.add(Apartamento(
                    numero_apartamento=a["numero_apto"],
                    nombre_torre=a["torre"],
                    piso=a["piso"],
                    conjunto_residencial_id=id_conjunto
                ))

            try:
                self.db.flush()

                # Actualizar total de apartamentos del conjunto
                self.db.execute(
                    update(ConjuntoResidencial)
                    .where(ConjuntoResidencial.id_conjunto_residencial == id_conjunto)
                    .values(numero_apartamentos=len(aptos_to_insert))
                    .execution_options(synchronize_session="fetch")
                )
                self.db.flush()
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
