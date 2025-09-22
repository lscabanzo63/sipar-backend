from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.infrastructure.db.models.model import Usuario

class UsuariosRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- NUEVO ----------
    def upsert_first_time(self, *, documento: str, nombre: str, apellidos: str,
                          telefono: str, email: str, contrasena: str) -> Usuario:
        """
        Crea o actualiza un usuario para el registro first-time.
        Criterio de upsert: documento OR email.
        Marca first_time=True.
        """
        doc = documento.strip()
        eml = email.lower().strip()

        stmt = select(Usuario).where(
            (Usuario.documento == doc) | (Usuario.email == eml)
        ).limit(1)
        user = self.db.execute(stmt).scalars().first()

        if user:
            user.nombre = nombre.strip()
            user.apellidos = apellidos.strip()
            user.telefono = telefono.strip()
            user.email = eml
            user.contrasena = contrasena.strip()
            user.first_time = True
            self.db.add(user)
            self.db.flush()
            return user

        user = Usuario(
            documento=doc,
            nombre=nombre.strip(),
            apellidos=apellidos.strip(),
            telefono=telefono.strip(),
            email=eml,
            contrasena=contrasena.strip(),
            first_time=True,
        )
        self.db.add(user)
        self.db.flush()
        return user
    # ---------------------------

    def get_by_email_and_pass(self, email: str, contrasena: str) -> Usuario | None:
        stmt = select(Usuario).where(
            Usuario.email == email.lower().strip(),
            Usuario.contrasena == contrasena.strip()
        ).limit(1)
        return self.db.execute(stmt).scalars().first()

    def disable_first_time(self, user_id: int) -> None:
        self.db.execute(
            update(Usuario)
            .where(Usuario.id_usuario == user_id)
            .values(first_time=False)
        )
        self.db.flush()

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
