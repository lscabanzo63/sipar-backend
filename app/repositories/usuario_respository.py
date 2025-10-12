import hmac
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from typing import Optional, List, Tuple
from app.infrastructure.db.models.model import Usuario, Apartamento

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
    
    def usuarios_del_conjunto(self, conjunto_id:int) -> List[dict]:
            sql = text("""
                SELECT u.id_usuario, u.tipo_usuario_id, u.administracion, a.id_apartamento
                FROM usuario u
                JOIN apartamento a ON a.usuario_id = u.id_usuario
                WHERE a.conjunto_residencial_id = :cid
            """)
            with self.engine.begin() as con:
                return [dict(r) for r in con.execute(sql, {"cid":conjunto_id}).mappings().all()]

    def conteo_ganados(self, ids: List[int]) -> dict:
        if not ids: return {}
        sql = text("""
                SELECT usuario_id, COUNT(*) AS c
                FROM resultado_sorteo_detalle
                WHERE usuario_id = ANY(:ids)
                GROUP BY usuario_id
            """)
        with self.engine.begin() as con:
                rows = con.execute(sql, {"ids": ids}).mappings().all()
                return {r["usuario_id"]: r["c"] for r in rows}