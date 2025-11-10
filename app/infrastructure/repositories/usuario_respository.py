import hmac
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from typing import Optional, List, Tuple
from app.infrastructure.db.models.model import Usuario, Apartamento, TipoUsuario

class UsuariosRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[Usuario]:
        stmt = (
            select(Usuario)
            .where(Usuario.email == (email or "").lower().strip())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def verify_password(self, plain_password: str, stored_password: str) -> bool:
        return hmac.compare_digest((plain_password or "").strip(), (stored_password or "").strip())

    def get_by_email_and_pass(self, email: str, contrasena: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(
            Usuario.email == email.lower().strip(),
            Usuario.contrasena == contrasena.strip()
        ).limit(1)
        return self.db.execute(stmt).scalars().first()

    def get_by_phone_and_pass(self, telefono: str, contrasena: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(
            Usuario.telefono == telefono.strip(),
            Usuario.contrasena == contrasena.strip()
        ).limit(1)
        return self.db.execute(stmt).scalars().first()

    def get_conjunto_id_for_user(self, user_id: int) -> Optional[int]:
        stmt = (
            select(Apartamento.conjunto_residencial_id)
            .where(Apartamento.usuario_id == user_id)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_user_with_role_by_email(self, email: str):
        stmt = (
            select(Usuario, TipoUsuario.nombre_tipo_usuario)
            .join(TipoUsuario, Usuario.tipo_usuario_id == TipoUsuario.id_tipo_usuario)
            .where(Usuario.email == email)
        )
        result = self.db.execute(stmt).first()
        if result:
            user, role = result
            return user, role
        return None, None
    