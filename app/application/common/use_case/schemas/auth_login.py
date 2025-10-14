from app.application.common.use_case.schemas.auth import LoginIn, LoginOut
from app.infrastructure.repositories.usuario_respository import UsuariosRepository

class AuthLoginUseCase:
    def __init__(self, repo: UsuariosRepository):
        self.repo = repo

    def execute(self, payload: LoginIn) -> LoginOut:
        # Primero intentamos por email (requerimiento actual)
        user = self.repo.get_by_email_and_pass(payload.email, payload.contrasena)
        
        if not user:
            raise ValueError("Credenciales inválidas")

        # Obtener id de conjunto por JOIN con apartamento
        conjunto_id = self.repo.get_conjunto_id_for_user(user.id_usuario)

        nombre_completo = f"{user.nombre.strip()} {user.apellidos.strip()}".strip()
        return LoginOut(
            id_usuario=user.id_usuario,
            email=getattr(user, "email", None),  # por si aún no está en el modelo
            nombre_completo=nombre_completo,
            first_time=bool(user.first_time),
            conjunto_residencial_id=conjunto_id,
        )
