from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class PoliticaCancelacion(BaseModel):
    tramo_gratuito_horas: int = Field(..., ge=0, description="Horas previas sin penalización")
    penalizacion_24h_porcentaje: float = Field(..., ge=0, le=100, description="Porcentaje de penalización 24h antes")
    penalizacion_mismo_dia_porcentaje: float = Field(..., ge=0, le=100, description="Porcentaje de penalización el mismo día")


class ReglaComercial:
    def __init__(
        self,
        tipo_servicio: str,
        porcentaje_comision_freemium: float,
        politica_cancelacion: PoliticaCancelacion,
        estado: str = "ACTIVO"
    ):
        self.tipo_servicio = tipo_servicio.strip().upper()
        self.porcentaje_comision_freemium = porcentaje_comision_freemium
        self.politica_cancelacion = politica_cancelacion
        self.estado = estado.strip().upper()

    def es_vigente(self) -> bool:
        """Verifica si la regla comercial se encuentra activa."""
        return self.estado == "ACTIVO"

    def to_response(self) -> dict:
        """Transforma la entidad de dominio al diccionario esperado por el contrato JSON."""
        return {
            "tipo_servicio": self.tipo_servicio,
            "porcentaje_comision_freemium": self.porcentaje_comision_freemium,
            "politica_cancelacion": self.politica_cancelacion.model_dump(),
            "estado": self.estado
        }


# — Schemas Pydantic (Validación de Entrada y Contratos de Salida) —

class ReglaComercialQuery(BaseModel):
    tipo_servicio: str = Field(..., min_length=1, description="Tipo de servicio a consultar")

    @field_validator("tipo_servicio")
    @classmethod
    def validar_formato_tipo_servicio(cls, v: str) -> str:
        valor_limpio = v.strip()
        if not valor_limpio:
            raise ValueError("El parámetro tipo_servicio es obligatorio")
        # Caso 5: Solo permite caracteres alfanuméricos y guion bajo (rechaza %&)
        if not re.match(r"^[a-zA-Z0-9_]+$", valor_limpio):
            raise ValueError("Formato de tipo de servicio no válido")
        return valor_limpio.upper()


class ReglaComercialDataResponse(BaseModel):
    tipo_servicio: str
    porcentaje_comision_freemium: float
    politica_cancelacion: PoliticaCancelacion
    estado: str


class ReglaComercialSuccessResponse(BaseModel):
    message: str = "Consulta de reglas comerciales exitosa"
    data: ReglaComercialDataResponse
    success: bool = True


class ReglaComercialErrorData(BaseModel):
    tipo_servicio: str
    porcentaje_comision_freemium: float = 0
    politica_cancelacion: Optional[PoliticaCancelacion] = None


class ReglaComercialErrorResponse(BaseModel):
    mensaje: str
    data: ReglaComercialErrorData
    success: bool = False