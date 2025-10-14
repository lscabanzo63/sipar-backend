# app/interfaces/schemas/sorteo_schemas.py
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, model_validator
from pydantic.config import ConfigDict


class PeriodicidadEnum(str, Enum):
    TRIMESTRAL = "TRIMESTRAL"
    CUATRIMESTRAL = "CUATRIMESTRAL"
    SEMESTRAL = "SEMESTRAL"


class ReglaTipoEnum(str, Enum):
    PRIORIDAD_PROPIETARIO = "PRIORIDAD_PROPIETARIO"
    PAGO_ADMINISTRACION = "PAGO_ADMINISTRACION"
    ROTACION = "ROTACION"


class ReglaIn(BaseModel):
    tipo: ReglaTipoEnum = Field(..., description="Tipo de norma")
    activa: bool = Field(..., description="Indica si la norma está activa")
    parametros: Optional[Dict[str, int]] = Field(
        default=None,
        description="Para ROTACION requiere { n: <int> }"
    )

    @model_validator(mode="after")
    def validar_rotacion(self) -> "ReglaIn":
        if self.activa and self.tipo == ReglaTipoEnum.ROTACION:
            n = None if not self.parametros else self.parametros.get("n")
            if n is None:
                raise ValueError("La norma ROTACION requiere parametros.n")
        return self


class ConfigIn(BaseModel):
    periodicidad: PeriodicidadEnum = Field(..., description="Periodicidad del ciclo")
    fecha_inicio: datetime = Field(
        ...,
        description="Fecha/hora de inicio del ciclo (se conservan día/hora)"
    )
    normas: List[ReglaIn] = Field(..., description="Listado de normas a aplicar")

    # 👇 Esto hace que Swagger muestre ejemplos listos para usar
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "TRIMESTRAL con ROTACION n=3 (válido)",
                    "value": {
                        "periodicidad": "TRIMESTRAL",
                        "fecha_inicio": "2026-01-15T00:00:00",
                        "normas": [
                            {"tipo": "PRIORIDAD_PROPIETARIO", "activa": True},
                            {"tipo": "PAGO_ADMINISTRACION", "activa": True},
                            {"tipo": "ROTACION", "activa": True, "parametros": {"n": 3}}
                        ]
                    }
                },
                {
                    "summary": "CUATRIMESTRAL con ROTACION n=2 (válido)",
                    "value": {
                        "periodicidad": "CUATRIMESTRAL",
                        "fecha_inicio": "2025-12-10T00:00:00",
                        "normas": [
                            {"tipo": "PAGO_ADMINISTRACION", "activa": True},
                            {"tipo": "ROTACION", "activa": True, "parametros": {"n": 2}}
                        ]
                    }
                },
                {
                    "summary": "SEMESTRAL con ROTACION n=2 (inválido)",
                    "value": {
                        "periodicidad": "SEMESTRAL",
                        "fecha_inicio": "2025-11-20T00:00:00",
                        "normas": [
                            {"tipo": "PRIORIDAD_PROPIETARIO", "activa": True},
                            {"tipo": "ROTACION", "activa": True, "parametros": {"n": 2}}
                        ]
                    }
                }
            ]
        }
    )


# ------- RESPUESTA -------

class ReglaOut(BaseModel):
    tipo: ReglaTipoEnum
    parametros: Optional[Dict[str, int]] = None


class ConfigOut(BaseModel):
    id_sorteo: int
    conjunto_id: int
    periodicidad: PeriodicidadEnum
    fechas_programadas: List[datetime]
    reglas_asignadas: List[ReglaOut]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_sorteo": 1,
                "conjunto_id": 1,
                "periodicidad": "TRIMESTRAL",
                "fechas_programadas": [
                    "2026-01-15T00:00:00",
                    "2026-04-15T00:00:00",
                    "2026-07-15T00:00:00",
                    "2026-10-15T00:00:00"
                ],
                "reglas_asignadas": [
                    {"tipo": "PRIORIDAD_PROPIETARIO"},
                    {"tipo": "PAGO_ADMINISTRACION"},
                    {"tipo": "ROTACION", "parametros": {"n": 3}}
                ]
            }
        }
    )
