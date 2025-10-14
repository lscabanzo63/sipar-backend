from app.application.common.use_case.schemas.auth import FirstTimeRegisterIn, LoginOut
from app.infrastructure.repositories.usuario_respository import UsuariosRepository

class FirstTimeRegisterUseCase:
    def __init__(self, users: UsuariosRepository):
        self.users = users

    def execute(self, payload: FirstTimeRegisterIn) -> LoginOut:
        user = self.users.upsert_first_time(
            documento=payload.documento,
            nombre=payload.nombre,
            apellidos=payload.apellidos,
            telefono=payload.telefono,
            email=payload.email,
            contrasena=payload.contrasena
        )
        nombre_completo = f"{user.nombre.strip()} {user.apellidos.strip()}".strip()
        return LoginOut(
            id_usuario=user.id_usuario,
            email=user.email,
            nombre_completo=nombre_completo,
            first_time=True
        )
