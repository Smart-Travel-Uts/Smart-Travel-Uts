
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


# --- 1. Schemas de ENTRADA y Validación (Pydantic) ---

class CatalogoInputValidation(BaseModel):
    tipo_catalogo: str = Field(..., min_length=2, description="Tipo de catálogo a consultar")

    @field_validator("tipo_catalogo")
    @classmethod
    def validar_sin_caracteres_especiales(cls, v: str) -> str:
        """
        Regla de dominio: El tipo de catálogo no debe contener símbolos extraños o vacíos.
        """
        limpio = v.strip().upper()
        if not limpio.isalnum() and "_" not in limpio:
            raise ValueError("Formato de catálogo no válido")
        return limpio


# --- 2. Schemas de SALIDA (Lo que devuelve la API al cliente) ---

class ItemCatalogoResponse(BaseModel):
    codigo: str
    descripcion: str
    estado: str

    class Config:
        from_attributes = True


class DataCatalogoResponse(BaseModel):
    tipo_catalogo: str
    total_items: int
    items: List[ItemCatalogoResponse]

    class Config:
        from_attributes = True


class CatalogoMasterResponse(BaseModel):
    message: Optional[str] = None
    mensaje: Optional[str] = None
    data: DataCatalogoResponse
    success: bool

    class Config:
        from_attributes = True


# --- 3. Modelos internos del dominio (Entidades reales y Reglas Rn-01 y Rn-02) ---

class ReglaComisionNegocio:
    """
    Rn-01: La comisión de la plataforma varía según el tipo de servicio reservado:
    8 % para vuelos, 10 % para hospedaje.
    """
    def __init__(self, tipo_servicio: str):
        self.tipo_servicio = tipo_servicio.strip().upper()

    def calcular_porcentaje(self) -> float:
        if self.tipo_servicio == "VUELO":
            return 8.0  # 8% para vuelos
        elif self.tipo_servicio == "HOSPEDAJE":
            return 10.0  # 10% para hospedaje
        return 0.0


class ReglaCancelacionNegocio:
    """
    Rn-02: Reglas de reembolso por anticipación de cancelación:
    - > 72 horas: 100% de reembolso.
    - Entre 24 y 72 horas: 50% de reembolso.
    - < 24 horas: 0% de reembolso.
    """
    def __init__(self, horas_anticipacion: int):
        self.horas_anticipacion = horas_anticipacion

    def calcular_reembolso(self) -> float:
        if self.horas_anticipacion > 72:
            return 100.0
        elif 24 <= self.horas_anticipacion <= 72:
            return 50.0
        else:
            return 0.0