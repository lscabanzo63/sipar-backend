from typing import Annotated, Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from pydantic.types import StringConstraints as S

TextoCorto = Annotated[str, S(min_length=2, max_length=100, strip_whitespace=True)]
Direccion  = Annotated[str, S(min_length=3, max_length=255, strip_whitespace=True)]
Tel        = Annotated[str, S(pattern=r'^\d{7,15}$', strip_whitespace=True)]

class SetupInitialOut(BaseModel):
    email: Optional[EmailStr] = None
    nombre_conjunto: str
    ciudad: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    cantidad_parqueaderos: int

class FieldError(BaseModel):
    field: str
    message: str
    code: str 

class SetupActionResult(BaseModel):
    status: str       # ok | validation_error | not_found | conflict | error
    message: str
    errors: Optional[List[FieldError]] = None

class SetupInitialUpdateIn(BaseModel):
    id_conjunto: int
    email: Optional[EmailStr] = None
    nombre_conjunto: TextoCorto
    ciudad: TextoCorto          
    direccion: Optional[Direccion] = None
    telefono: Optional[Tel] = None
    cantidad_parqueaderos: int

    @field_validator("id_conjunto")
    @classmethod
    def positive_int(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Debe ser un entero positivo")
        return v

    @field_validator("cantidad_parqueaderos")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("La cantidad de parqueaderos no puede ser negativa")
        return v
