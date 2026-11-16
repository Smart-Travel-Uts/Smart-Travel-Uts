from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
import re

# — Schema de ENTRADA / Validación de formato de clave —
class ParametroGlobalQuery(BaseModel):
    clave: str = Field(..., min_length=1, description="Clave única del parámetro global")

    @field_validator("clave")
    @classmethod
    def validar_formato_clave(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Formato de clave no válido")
        return v.strip()


# — Schemas de SALIDA (Contratos JSON para la API) —
class ParametroGlobalDataResponse(BaseModel):
    clave: str
    modulo: str
    valor: str
    tipo_dato: str
    estado: str

    class Config:
        from_attributes = True


class ParametroGlobalSuccessResponse(BaseModel):
    message: str = "Consulta de parámetro global exitosa"
    data: ParametroGlobalDataResponse
    success: bool = True


class ParametroGlobalErrorResponse(BaseModel):
    mensaje: str
    data: Optional[dict] = None
    success: bool = False


# — Modelo interno del dominio (la "entidad real" con reglas de negocio) —
class ParametroGlobal:
    def __init__(self, clave: str, modulo: str, valor: str, tipo_dato: str, estado: str, es_interno: bool = False):
        self.clave = clave
        self.modulo = modulo
        self.valor = valor
        self.tipo_dato = tipo_dato
        self.estado = estado
        self.es_interno = es_interno

    # REGLA DE NEGOCIO: ¿El parámetro se encuentra activo y vigente?
    def es_vigente(self) -> bool:
        return self.estado == "ACTIVO"

    # REGLA DE NEGOCIO: ¿Es un parámetro público permitido para consulta externa?
    def es_publico(self) -> bool:
        return not self.es_interno

    # Método de conversión para la respuesta
    def to_response(self) -> dict:
        return {
            "clave": self.clave,
            "modulo": self.modulo,
            "valor": self.valor,
            "tipo_dato": self.tipo_dato,
            "estado": self.estado
        }