from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional

class NormaConfig(BaseModel):
    tipo: str
    activa: bool
    parametros: Optional[dict] = None

class SorteoConfigCreate(BaseModel):
    periodicidad: str = Field(..., example="TRIMESTRAL")
    fecha_inicio: datetime = Field(..., example="2026-01-15T00:00:00")
    normas: List[NormaConfig] = Field(..., min_items=1)

    @validator('periodicidad')
    def validate_periodicidad(cls, v):
        allowed = ["TRIMESTRAL", "CUATRIMESTRAL", "SEMESTRAL"]
        if v.upper() not in allowed:
            raise ValueError("Periodicidad inválida")
        return v.upper()
    
class EjecutarSorteoRequest(BaseModel):
    id_conjunto: int = Field(..., gt=0)
    fecha_actual: datetime = Field(...)

class GanadorResumen(BaseModel):
    usuario_id: int = Field(..., gt=0, description="ID del usuario ganador")
    nombre: str = Field(..., min_length=1, description="Nombre completo del usuario")
    numero_parqueadero: int = Field(..., gt=0, description="Número de parqueadero asignado")

class EjecutarSorteoRequest(BaseModel):
    id_conjunto: int = Field(..., gt=0, description="ID del conjunto residencial")
    fecha_actual: datetime = Field(
        default_factory=datetime.now,
        description="Fecha actual para el sorteo"
    )

class EjecutarSorteoResponse(BaseModel):
    id_resultado_sorteo: int = Field(..., gt=0, description="ID del resultado del sorteo")
    mensaje: str = Field(..., description="Mensaje del resultado del sorteo")
    ganadores: List[GanadorResumen] = Field(
        ..., 
        description="Lista de ganadores del sorteo",
        min_items=1
    )
    fecha_sorteo: datetime = Field(..., description="Fecha en que se realizó el sorteo")

class ResultadoSorteoResponse(BaseModel):
    id_resultado_sorteo: int = Field(..., gt=0)
    fecha: datetime
    ganadores: List[GanadorResumen]
    estado: bool = Field(..., description="Estado del resultado del sorteo")

    class Config:
        json_schema_extra = {
            "example": {
                "id_resultado_sorteo": 1,
                "fecha": "2026-01-15T00:00:00",
                "ganadores": [
                    {
                        "usuario_id": 1,
                        "nombre": "Juan Pérez",
                        "numero_parqueadero": 5
                    }
                ],
                "estado": True
            }
        }