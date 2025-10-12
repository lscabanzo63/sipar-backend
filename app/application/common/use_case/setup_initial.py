from app.application.common.use_case.schemas.setup_schemas import (
    SetupInitialOut, SetupInitialUpdateIn, SetupActionResult, FieldError, TorresConfigIn
)
from app.repositories.setup_repository import SetupRepository

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

    def execute(self, payload: TorresConfigIn) -> dict:
        if payload.numeracion_automatica != "NUMERACION_AUTOMATICA":
            raise ValueError("numeracion_automatica inválida")

        resultado = self.repo.generar_apartamentos_preservando_asignaciones(
            id_conjunto=payload.id_conjunto,
            torres=payload.num_torres,
            pisos_x_torre=payload.pisos_x_torre,
            aptos_x_piso=payload.aptos_x_piso,
            reset_parqueadero=True,  # ponlo en False si no quieres tocarlo nunca
        )
        return resultado
