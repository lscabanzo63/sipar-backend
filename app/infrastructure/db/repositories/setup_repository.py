from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from app.infrastructure.db.models.model import (
    ConjuntoResidencial, Ciudad, Usuario, Apartamento
)

class SetupRepository:
    def __init__(self, db: Session):
        self.db = db

    def fetch_initial(self, id_conjunto: int, id_usuario: int):
        # Obtener el usuario (aunque no se use para la cantidad de parqueaderos)
        usr = self.db.get(Usuario, id_usuario)

        # Obtener el conjunto residencial
        cjto = self.db.get(ConjuntoResidencial, id_conjunto)

        # Obtener el nombre de la ciudad
        ciudad_nombre: Optional[str] = None
        if cjto and cjto.ciudad_id:
            ciudad = self.db.get(Ciudad, cjto.ciudad_id)
            ciudad_nombre = ciudad.nombre_ciudad if ciudad else None

        # Cantidad total de parqueaderos del conjunto
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
    #
        ciudad_id = ciudad_row.id_ciudad

        asignados = self.db.scalar(
            select(func.count(func.distinct(Apartamento.parqueadero_id)))
            .where(Apartamento.conjunto_residencial_id == id_conjunto)
            .where(Apartamento.parqueadero_id.isnot(None))
        ) or 0
        if cantidad_parqueaderos < asignados:
            return 409

        # Limpieza
        nombre_conjunto = " ".join(nombre_conjunto.split())
        direccion = " ".join(direccion.split()) if direccion else None
        email = email.lower().strip() if email else None
        telefono = telefono.strip() if telefono else None

        # Persistir en CONJUNTO
        cjto.nombre_conjunto = nombre_conjunto
        cjto.direccion_conjunto = direccion
        cjto.ciudad_id = ciudad_id
        cjto.numero_apartamentos = cantidad_parqueaderos
        cjto.email_contacto = email
        cjto.telefono_contacto = telefono

        self.db.add(cjto)
        self.db.flush()
        return 200
    

    def get_conjunto(self, id_conjunto: int) -> Optional[ConjuntoResidencial]:
        return self.db.get(ConjuntoResidencial, id_conjunto)

    def get_usuario(self, id_usuario: int):
        return self.db.get(Usuario, id_usuario)

    def update_numero_torres(self, id_conjunto: int, numero_torres: int):
        res = self.db.execute(
            update(ConjuntoResidencial)
            .where(ConjuntoResidencial.id_conjunto_residencial == id_conjunto)
            .values(numero_torres=numero_torres)
            .execution_options(synchronize_session="fetch")
        )
        self.db.flush()
        return res.rowcount

    def marcar_first_time_false(self, id_usuario: int):
        res = self.db.execute(
            update(Usuario)
            .where(Usuario.id_usuario == id_usuario)
            .values(first_time=False)
            .execution_options(synchronize_session="fetch")
        )
        return res.rowcount

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
