import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

ID_VUELO_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
COMISION_PLATAFORMA_PORCENTAJE = 8.00


# ── Schema de ENTRADA / VALIDACIÓN de id_vuelo ────────────────
class OfertaVueloConsultaRequest(BaseModel):
    id_vuelo: str = Field(..., min_length=3, max_length=20, description="Identificador de la oferta de vuelo")

    # ── REGLA DE NEGOCIO: formato válido de id_vuelo ──────────
    @field_validator("id_vuelo")
    @classmethod
    def validar_formato_id_vuelo(cls, v: str) -> str:
        limpio = v.strip().upper()
        if not ID_VUELO_REGEX.match(limpio):
            raise ValueError("El formato del identificador de vuelo (id_vuelo) no es válido")
        return limpio


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ────
class DesglosePrecioResponse(BaseModel):
    precio_base: float
    comision_plataforma_porcentaje: float
    monto_comision: float
    impuestos_tasas: float
    precio_total: float
    moneda: str = "COP"

    model_config = ConfigDict(from_attributes=True)


class OfertaVueloDetalleResponse(BaseModel):
    id_vuelo: str
    aerolinea: str
    numero_vuelo: str
    origen: str
    destino: str
    hora_salida: str
    hora_llegada: str
    duracion_total: str
    escalas: int
    equipaje_permitido: str
    desglose_precio: DesglosePrecioResponse
    politica_cancelacion: str

    model_config = ConfigDict(from_attributes=True)


class DetalleOfertaApiResponse(BaseModel):
    message: str
    data: Optional[OfertaVueloDetalleResponse] = None
    success: bool


class OfertaNoDisponibleResponse(BaseModel):
    mensaje: str
    data: None = None
    success: bool = False


# ── Modelo interno del dominio (la "entidad real") ────────────
class OfertaVuelo:
    def __init__(
        self,
        id_vuelo: str,
        aerolinea: str,
        numero_vuelo: str,
        origen: str,
        destino: str,
        hora_salida: str,
        hora_llegada: str,
        duracion_total: str,
        escalas: int,
        equipaje_permitido: str,
        precio_base: float,
        impuestos_tasas: float,
        politica_cancelacion: str,
        moneda: str = "COP",
        disponible: bool = True,
    ) -> None:
        self.id_vuelo = id_vuelo
        self.aerolinea = aerolinea
        self.numero_vuelo = numero_vuelo
        self.origen = origen.upper()
        self.destino = destino.upper()
        self.hora_salida = hora_salida
        self.hora_llegada = hora_llegada
        self.duracion_total = duracion_total
        self.escalas = escalas
        self.equipaje_permitido = equipaje_permitido
        self.precio_base = round(float(precio_base), 2)
        self.impuestos_tasas = round(float(impuestos_tasas), 2)
        self.politica_cancelacion = politica_cancelacion
        self.moneda = moneda
        self.disponible = disponible

    # REGLA DE NEGOCIO: ¿la oferta está activa y disponible?
    def esta_disponible(self) -> bool:
        return self.disponible

    # REGLA DE NEGOCIO (Prs-16): calcular comisión del 8% y total
    def calcular_desglose(
        self, comision_porcentaje: float = COMISION_PLATAFORMA_PORCENTAJE
    ) -> dict:
        comision_pct = round(float(comision_porcentaje), 2)
        monto_comision = round(self.precio_base * (comision_pct / 100.0), 2)
        precio_total = round(
            self.precio_base + monto_comision + self.impuestos_tasas, 2
        )
        return {
            "precio_base": self.precio_base,
            "comision_plataforma_porcentaje": comision_pct,
            "monto_comision": monto_comision,
            "impuestos_tasas": self.impuestos_tasas,
            "precio_total": precio_total,
            "moneda": self.moneda,
        }

    def to_response(
        self, comision_porcentaje: float = COMISION_PLATAFORMA_PORCENTAJE
    ) -> dict:
        return {
            "id_vuelo": self.id_vuelo,
            "aerolinea": self.aerolinea,
            "numero_vuelo": self.numero_vuelo,
            "origen": self.origen,
            "destino": self.destino,
            "hora_salida": self.hora_salida,
            "hora_llegada": self.hora_llegada,
            "duracion_total": self.duracion_total,
            "escalas": self.escalas,
            "equipaje_permitido": self.equipaje_permitido,
            "desglose_precio": self.calcular_desglose(comision_porcentaje),
            "politica_cancelacion": self.politica_cancelacion,
        }


# ── Excepciones de dominio (mapeadas a 400 / 404 / 503) ───────
class ValidacionOfertaError(ValueError):
    """Error de validación en el identificador de oferta (HTTP 400)."""


class OfertaNoDisponibleError(Exception):
    """Error cuando la oferta no existe o caducó (HTTP 404)."""


class ProveedorOfertaError(Exception):
    """Error de conexión o disponibilidad con BD o proveedor (HTTP 503)."""