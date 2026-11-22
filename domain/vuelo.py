from typing import List, Optional
from pydantic import BaseModel, Field


class Vuelo:
    def __init__(
        self,
        id_vuelo: str,
        aerolinea: str,
        origen: str,
        destino: str,
        fecha_salida: str,
        precio_base: float,
        asientos_disponibles: int,
        moneda: str = "COP",
        fecha_retorno: Optional[str] = None,
    ) -> None:
        self.id_vuelo = id_vuelo
        self.aerolinea = aerolinea
        self.origen = origen
        self.destino = destino
        self.fecha_salida = fecha_salida
        self.precio_base = round(float(precio_base), 2)
        self.moneda = moneda
        self.asientos_disponibles = asientos_disponibles
        self.fecha_retorno = fecha_retorno

    def tiene_asientos(self, pasajeros: int = 1) -> bool:
        return self.asientos_disponibles >= pasajeros

    def calcular_cotizacion(
        self, pasajeros: int = 1, incluye_retorno: bool = False
    ) -> float:
        factor_trayecto = 2 if incluye_retorno else 1
        return round(self.precio_base * pasajeros * factor_trayecto, 2)

    def to_dict(
        self, pasajeros: int = 1, incluye_retorno: bool = False
    ) -> dict:
        return {
            "id_vuelo": self.id_vuelo,
            "aerolinea": self.aerolinea,
            "origen": self.origen,
            "destino": self.destino,
            "fecha_salida": self.fecha_salida,
            "fecha_retorno": self.fecha_retorno,
            "precio_base": self.precio_base,
            "cotizacion_total": self.calcular_cotizacion(
                pasajeros=pasajeros, incluye_retorno=incluye_retorno
            ),
            "moneda": self.moneda,
            "asientos_disponibles": self.asientos_disponibles,
        }


class VueloItemSchema(BaseModel):
    id_vuelo: str
    aerolinea: str
    origen: str
    destino: str
    fecha_salida: str
    fecha_retorno: Optional[str] = None
    precio_base: float
    cotizacion_total: float
    moneda: str = "COP"
    asientos_disponibles: int


class BusquedaVuelosDataSchema(BaseModel):
    total_resultados: int
    vuelos: List[VueloItemSchema] = Field(default_factory=list)


class BusquedaVuelosResponseSchema(BaseModel):
    message: str
    data: BusquedaVuelosDataSchema
    success: bool


class ValidacionVueloError(Exception):
    """Error de validación en los parámetros de búsqueda de vuelos (HTTP 400)."""


class ProveedorVuelosError(Exception):
    """Error de comunicación o disponibilidad del proveedor externo de vuelos (HTTP 503)."""