from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.infrastructure.db.models.model import (
    ConjuntoResidencial, Ciudad, Usuario, Apartamento
)

class SetupRepository:
    def __init__(self, db: Session):
        self.db = db

    def fetch_initial(self, id_conjunto: int, id_usuario: int):
        usr = self.db.get(Usuario, id_usuario)
        cjto = self.db.get(ConjuntoResidencial, id_conjunto)

        ciudad_nombre: Optional[str] = None
        if cjto and cjto.ciudad_id:
            ciudad = self.db.get(Ciudad, cjto.ciudad_id)
            ciudad_nombre = ciudad.nombre_ciudad if ciudad else None

        asignados = self.db.scalar(
            select(func.count(func.distinct(Apartamento.parqueadero_id)))
            .where(Apartamento.conjunto_residencial_id == id_conjunto)
            .where(Apartamento.parqueadero_id.isnot(None))
        ) or 0

        return usr, cjto, ciudad_nombre, asignados

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
