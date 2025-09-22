# app/application/common/use_case/schemas/auth.py
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, field_validator
from pydantic.types import StringConstraints as S

# --- Tipos validados ---

# Documento: solo dígitos, 5–30
Doc = Annotated[str, S(pattern=r'^\d{5,30}$', strip_whitespace=True)]

# Nombre/Apellidos: letras con tildes y ñ, 2–100
TextoNombre = Annotated[str, S(
    pattern=r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,100}$',
    strip_whitespace=True
)]

# Teléfono: solo dígitos, 7–15
Tel = Annotated[str, S(pattern=r'^\d{7,15}$', strip_whitespace=True)]

# Contraseña: mínimo 6, máx 255
Contrasena = Annotated[str, S(min_length=6, max_length=255, strip_whitespace=True)]


# --- DTOs ---

class FirstTimeRegisterIn(BaseModel):
    documento: Doc
    nombre: TextoNombre
    apellidos: TextoNombre
    telefono: Tel
    email: EmailStr
    contrasena: Contrasena

    @field_validator("nombre", "apellidos")
    @classmethod
    def collapse_spaces(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        # devolver string; Pydantic lo valida como EmailStr
        return v.lower().strip()


class LoginIn(BaseModel):
    email: EmailStr
    contrasena: Contrasena

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class LoginOut(BaseModel):
    id_usuario: int
    email: Optional[str] = None
    nombre_completo: str
    first_time: bool
    conjunto_residencial_id: Optional[int] = None  
