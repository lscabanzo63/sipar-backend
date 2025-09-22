from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.infrastructure.db.models.model import Usuario  # usa tu modelo ya generado

class UsuariosRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_phone_and_pass(self, telefono: str, contrasena: str) -> Usuario | None:
        telefono = " ".join(telefono.strip().split())
        contrasena = contrasena.strip()
        stmt = (
            select(Usuario)
            .where(Usuario.telefono == telefono)
            .where(Usuario.contrasena == contrasena)
            .limit(1)
        )
        return self.db.scalar(stmt)

    def set_first_time(self, user_id: int, first_time: bool) -> int:
        res = self.db.execute(
            update(Usuario)
            .where(Usuario.id_usuario == user_id)
            .values(first_time=first_time)
            .execution_options(synchronize_session="fetch")
        )
        return res.rowcount

    def get_by_id(self, user_id: int) -> Usuario | None:
        return self.db.get(Usuario, user_id)
