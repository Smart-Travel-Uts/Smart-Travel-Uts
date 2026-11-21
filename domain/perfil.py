from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

MONEDAS_SOPORTADAS = {"USD", "COP", "EUR", "MXN", "BRL"}
IDIOMAS_SOPORTADOS = {"ES", "EN", "PT", "FR"}


class PreferenciasViajero(BaseModel):
    """Preferencias configurables de idioma, moneda base e intereses del viajero."""

    idioma: str = Field(
        default="ES",
        description="Idioma preferido del usuario (ej. ES, EN)"
    )
    moneda_base: str = Field(
        default="USD",
        description="Moneda base del catálogo maestro (ej. USD, COP, EUR)"
    )
    categorias_interes: List[str] = Field(
        default_factory=lambda: ["GASTRONOMIA", "PLAYA"],
        description="Categorías turísticas de interés"
    )

    @field_validator("moneda_base")
    @classmethod
    def validar_moneda_base(cls, valor: str) -> str:
        if valor is None or not valor.strip():
            raise ValueError("La moneda seleccionada no es válida")
        moneda = valor.strip().upper()
        if moneda not in MONEDAS_SOPORTADAS:
            raise ValueError("La moneda seleccionada no es válida")
        return moneda

    @field_validator("idioma")
    @classmethod
    def validar_idioma(cls, valor: str) -> str:
        if valor is None or not valor.strip():
            raise ValueError("El idioma seleccionado no es válido")
        idioma = valor.strip().upper()
        if idioma not in IDIOMAS_SOPORTADOS:
            raise ValueError("El idioma seleccionado no es válido")
        return idioma

    @field_validator("categorias_interes")
    @classmethod
    def normalizar_categorias(cls, categorias: List[str]) -> List[str]:
        return [cat.strip().upper() for cat in categorias if cat and cat.strip()]


class PerfilUsuario(BaseModel):
    """Entidad de dominio con los datos personales y preferencias del viajero."""

    usuario_id: str = Field(..., description="Identificador único del usuario")
    nombre_completo: str = Field(..., description="Nombre completo del viajero")
    correo: str = Field(..., description="Correo electrónico registrado")
    preferencias: PreferenciasViajero = Field(
        default_factory=PreferenciasViajero,
        description="Preferencias del viajero"
    )


class ActualizarPerfilRequest(BaseModel):
    """Esquema de entrada para actualizar datos personales y preferencias del viajero."""

    nombre_completo: Optional[str] = Field(
        default=None,
        description="Nombre completo actualizado del viajero"
    )
    idioma: Optional[str] = Field(
        default=None,
        description="Idioma preferido (ej. ES, EN)"
    )
    moneda_base: Optional[str] = Field(
        default=None,
        description="Moneda base del catálogo maestro (ej. USD, COP, EUR)"
    )
    categorias_interes: Optional[List[str]] = Field(
        default=None,
        description="Lista actualizada de categorías turísticas de interés"
    )

    @field_validator("nombre_completo")
    @classmethod
    def validar_nombre_completo(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        limpio = valor.strip()
        if not limpio:
            raise ValueError("El nombre completo no puede estar vacío")
        return limpio

    @field_validator("moneda_base")
    @classmethod
    def validar_moneda_actualizacion(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        moneda = valor.strip().upper()
        if moneda not in MONEDAS_SOPORTADAS:
            raise ValueError("La moneda seleccionada no es válida")
        return moneda

    @field_validator("idioma")
    @classmethod
    def validar_idioma_actualizacion(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        idioma = valor.strip().upper()
        if idioma not in IDIOMAS_SOPORTADOS:
            raise ValueError("El idioma seleccionado no es válido")
        return idioma

    @field_validator("categorias_interes")
    @classmethod
    def normalizar_categorias_actualizacion(
        cls, categorias: Optional[List[str]]
    ) -> Optional[List[str]]:
        if categorias is None:
            return None
        return [cat.strip().upper() for cat in categorias if cat and cat.strip()]


class PerfilSuccessResponse(BaseModel):
    """Respuesta JSON estándar cuando la consulta o actualización es exitosa."""

    message: str = "Consulta de perfil exitosa"
    data: PerfilUsuario
    success: bool = True


class PerfilErrorResponse(BaseModel):
    """Respuesta JSON estándar para errores de autenticación, validación o servicio."""

    mensaje: str
    data: Optional[dict] = None
    success: bool = False