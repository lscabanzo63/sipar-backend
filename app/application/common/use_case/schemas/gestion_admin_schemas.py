from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Optional

class ConjuntoIn(BaseModel):
    nombre: str
    direccion: str
    numero_torres: int = Field(gt=0)
    numero_apartamentos: int = Field(gt=0)
    ciudad: Literal["Bogotá", "Medellín", "Cali"]
    email_conjunto: EmailStr
    telefono_conjunto: str
    numero_parqueaderos: int = Field(ge=0)

class AdminIn(BaseModel):
    nombres: str
    apellidos: str
    email: EmailStr
    telefono: str
    documento: str

class CrearAdminRequest(BaseModel):
    conjunto: ConjuntoIn
    admin: AdminIn

class AdminItemOut(BaseModel):
    id_usuario: int
    nombres: str
    apellidos: str
    email: EmailStr
    telefono: str
    conjunto: str
    estado: bool

class ToggleEstadoRequest(BaseModel):
    accion: Literal["Bloqueo", "Desbloqueo"]

class ModificarAdminRequest(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    documento: Optional[str] = None
