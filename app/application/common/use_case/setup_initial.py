from app.application.common.use_case.schemas.setup import (
    SetupInitialOut, SetupInitialUpdateIn, SetupActionResult, FieldError
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
    def __init__(self, repo: SetupRepository):
        self.repo = repo

    def execute(self, payload: SetupInitialUpdateIn) -> SetupActionResult:
        # Validación “espacios en blanco”
        errors: list[FieldError] = []
        def is_blank(s: str | None) -> bool:
            return s is not None and s.strip() == ""

        if is_blank(payload.nombre_conjunto):
            errors.append(FieldError(field="nombre_conjunto", code="blank", message="El nombre no puede estar vacío"))
        if payload.direccion is not None and is_blank(payload.direccion):
            errors.append(FieldError(field="direccion", code="blank", message="La dirección no puede estar vacía"))
        if payload.email is not None and is_blank(payload.email):
            errors.append(FieldError(field="email", code="blank", message="El correo no puede estar vacío"))
        if payload.telefono is not None and is_blank(payload.telefono):
            errors.append(FieldError(field="telefono", code="blank", message="El teléfono no puede estar vacío"))

        if errors:
            return SetupActionResult(status="validation_error", message="Datos inválidos", errors=errors)

        code = self.repo.update_initial(
            id_conjunto=payload.id_conjunto,
            email=(payload.email.lower().strip() if payload.email else None),
            nombre_conjunto=payload.nombre_conjunto,
            ciudad_id=payload.ciudad_id,
            direccion=payload.direccion,
            telefono=payload.telefono,
            cantidad_parqueaderos=payload.cantidad_parqueaderos,
        )

        if code == 404:
            return SetupActionResult(status="not_found", message="Conjunto no encontrado")
        if code == 409:
            return SetupActionResult(
                status="conflict",
                message="La cantidad de parqueaderos no puede ser menor a la ya asignada en el conjunto"
            )

        return SetupActionResult(status="ok", message="Datos guardados correctamente")
