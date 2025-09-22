from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, Tuple

from app.infrastructure.db.models.model import Usuario, Apartamento  # Apartamento tiene conjunto_residencial_id :contentReference[oaicite:2]{index=2}

class UsuariosRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email_and_pass(self, email: str, contrasena: str) -> Optional[Usuario]:
        # Si tu tabla usuario NO tiene email todavía, comenta este método y usa el de teléfono.
        stmt = select(Usuario).where(
            Usuario.email == email.lower().strip(),
            Usuario.contrasena == contrasena.strip()
        ).limit(1)
        return self.db.execute(stmt).scalars().first()

    def get_by_phone_and_pass(self, telefono: str, contrasena: str) -> Optional[Usuario]:
        # Fallback si aún no tienes email en BD/ORM
        stmt = select(Usuario).where(
            Usuario.telefono == telefono.strip(),
            Usuario.contrasena == contrasena.strip()
        ).limit(1)
        return self.db.execute(stmt).scalars().first()

    def get_conjunto_id_for_user(self, user_id: int) -> Optional[int]:
        # Apartamento.usuario_id -> Apartamento.conjunto_residencial_id (JOIN implícito)
        stmt = (
            select(Apartamento.conjunto_residencial_id)
            .where(Apartamento.usuario_id == user_id)
            .limit(1)
        )
        res = self.db.execute(stmt).scalar_one_or_none()
        return res
