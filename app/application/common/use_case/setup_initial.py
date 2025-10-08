from app.application.common.use_case.schemas.setup_schemas import (
    SetupInitialOut, SetupInitialUpdateIn, SetupActionResult, FieldError, TorresConfigIn
)
from app.infrastructure.db.repositories.setup_repository import SetupRepository

class SetupInitialGetUseCase:
    def __init__(self, repo: SetupRepository):
        self.repo = repo

    def execute(self, id_conjunto: int, id_usuario: int) -> SetupInitialOut:
        usr, cjto, ciudad_nombre, asignados = self.repo.fetch_initial(id_conjunto, id_usuario)
        if not cjto:
            raise ValueError("Conjunto residencial no encontrado")

        return SetupInitialOut(
            email=getattr(cjto, "email_contacto", None),
            nombre_conjunto=cjto.nombre_conjunto,
            ciudad=ciudad_nombre or "",
            direccion=cjto.direccion_conjunto,
            telefono=getattr(cjto, "telefono_contacto", None),
            cantidad_parqueaderos=cjto.numero_apartamentos if cjto.numero_apartamentos is not None else asignados,
        )

class SetupInitialUpdateUseCase:
    def __init__(self, repo):
        self.repo = repo

    def execute(self, payload: SetupInitialUpdateIn) -> SetupActionResult:
        code = self.repo.update_initial(
            id_conjunto=payload.id_conjunto,
            email=payload.email,
            nombre_conjunto=payload.nombre_conjunto,
            ciudad=payload.ciudad,
            direccion=payload.direccion,
            telefono=payload.telefono,
            cantidad_parqueaderos=payload.cantidad_parqueaderos,
        )
        if code == 200:
            return SetupActionResult(status="ok", message="Configuración guardada")
        if code == 404:
            return SetupActionResult(status="not_found", message="Conjunto o ciudad no existe")
        if code == 409:
            return SetupActionResult(status="conflict", message="Capacidad menor a parqueaderos asignados")
        return SetupActionResult(status="error", message="Error no controlado")
    
class ConfigTorresUseCase:
    def __init__(self, repo: SetupRepository):
        self.repo = repo

    def execute(self, payload: TorresConfigIn):
        """
        Genera y guarda apartamentos para un conjunto residencial según
        torres, pisos por torre y apartamentos por piso.
        """
        # Obtener conjunto y usuario
        conjunto = self.repo.get_conjunto(payload.id_conjunto)
        if not conjunto:
            raise ValueError("Conjunto no encontrado")

        usuario = self.repo.get_usuario(payload.id_usuario)
        if not usuario:
            raise ValueError("Usuario no encontrado")

        # Validar numeración automática
        if payload.numeracion_automatica.strip().upper() != "NUMERACION_AUTOMATICA":
            raise ValueError("Valor de numeracion_automatica inválido")

        # Generar apartamentos automáticamente dentro del repository
        self.repo.generar_apartamentos(
            id_conjunto=payload.id_conjunto,
            torres=payload.num_torres,
            pisos_x_torre=payload.pisos_x_torre,
            aptos_x_piso=payload.aptos_x_piso
        )

        # Actualizar número total de torres
        self.repo.update_numero_torres(payload.id_conjunto, payload.num_torres)

        # Marcar first_time = False para el usuario que ejecuta
        self.repo.marcar_first_time_false(payload.id_usuario)

        # Respuesta final
        total_apartamentos = payload.num_torres * payload.pisos_x_torre * payload.aptos_x_piso
        return {
            "status": "ok",
            "message": f"Apartamentos generados correctamente: {total_apartamentos} aptos en {payload.num_torres} torres"
        }
