# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

import math
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

RADIO_MAXIMO_KM = 50.0
CATEGORIAS_POI = Literal[
    "GASTRONOMIA",
    "CULTURA",
    "PARQUE_CULTURAL",
    "TRANSPORTE",
    "HISTORIA",
]


# ── Schema de ENTRADA (lo que recibe/valida la API) ──────────
class BusquedaPoisQuery(BaseModel):
    latitud:   float                  = Field(..., description="Coordenada WGS84 de origen (-90.0 a 90.0)")
    longitud:  float                  = Field(..., description="Coordenada WGS84 de origen (-180.0 a 180.0)")
    radio_km:  float                  = Field(3.0, description="Radio geográfico de cobertura (> 0 y <= 50)")
    categoria: Optional[CATEGORIAS_POI] = Field(None, description="Categoría específica del POI")
    limite:    int                    = Field(50, ge=1, le=200, description="Límite de POIs a retornar")

    # ── REGLA DE NEGOCIO: latitud entre -90.0 y 90.0 ────────
    @field_validator("latitud")
    @classmethod
    def latitud_valida(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("La latitud debe estar dentro del rango [-90.0, 90.0]")
        return round(float(v), 6)

    # ── REGLA DE NEGOCIO: longitud entre -180.0 y 180.0 ─────
    @field_validator("longitud")
    @classmethod
    def longitud_valida(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("La longitud debe estar dentro del rango [-180.0, 180.0]")
        return round(float(v), 6)

    # ── REGLA DE NEGOCIO: radio > 0 y <= 50 km con 2 dec. ───
    @field_validator("radio_km")
    @classmethod
    def radio_valido(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("El radio en kilómetros debe ser un número positivo mayor a 0")
        if v > RADIO_MAXIMO_KM:
            raise ValueError("El radio en kilómetros no puede superar los 50 km")
        return round(float(v), 2)

    # ── REGLA DE NEGOCIO: normalizar y validar categoría ────
    @field_validator("categoria", mode="before")
    @classmethod
    def categoria_valida(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        limpia = str(v).strip().upper()
        if not limpia:
            return None
        permitidas = {"GASTRONOMIA", "CULTURA", "PARQUE_CULTURAL", "TRANSPORTE", "HISTORIA"}
        if limpia not in permitidas:
            raise ValueError(
                "Categoría inválida. Valores permitidos: GASTRONOMIA, CULTURA, PARQUE_CULTURAL, TRANSPORTE, HISTORIA"
            )
        return limpia


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ────
class CentroBusquedaResponse(BaseModel):
    latitud:  float
    longitud: float


class UbicacionGeoJsonResponse(BaseModel):
    type:        Literal["Point"] = "Point"
    coordinates: list[float]


class PuntoInteresResponse(BaseModel):
    id_poi:              str
    nombre:              str
    categoria:           str
    ubicacion:           UbicacionGeoJsonResponse
    distancia_km:        float
    calificacion_promedio: float
    direccion:           str
    horario_apertura:    str
    horario_cierre:      str
    estado_operativo:    str

    model_config = ConfigDict(from_attributes=True)


class MapaPoisDataResponse(BaseModel):
    centro_busqueda: CentroBusquedaResponse
    radio_aplicado_km: float
    total_pois:        int
    puntos_interes:    list[PuntoInteresResponse]


class MapaPoisResponse(BaseModel):
    message: str
    data:    MapaPoisDataResponse
    success: bool = True


class ErrorNavegacionDataResponse(BaseModel):
    errores: list[str]


class ErrorNavegacionResponse(BaseModel):
    message: str
    data:    ErrorNavegacionDataResponse
    success: bool = False


# ── Modelo interno del dominio (la "entidad real") ────────────
class PuntoInteres:
    def __init__(
        self,
        id_poi: str,
        nombre: str,
        categoria: str,
        latitud: float,
        longitud: float,
        calificacion_promedio: float,
        direccion: str,
        horario_apertura: str,
        horario_cierre: str,
        estado_operativo: str = "ABIERTO",
        activo: bool = True,
    ):
        self.id_poi               = id_poi.strip().upper()
        self.nombre               = nombre.strip()
        self.categoria            = categoria.strip().upper()
        self.latitud              = float(latitud)
        self.longitud             = float(longitud)
        self.calificacion_promedio = round(float(calificacion_promedio), 2)
        self.direccion            = direccion.strip()
        self.horario_apertura     = horario_apertura.strip()
        self.horario_cierre       = horario_cierre.strip()
        self.estado_operativo     = estado_operativo.strip().upper()
        self.activo               = bool(activo)

    # REGLA DE NEGOCIO: distancia en km usando fórmula de Haversine
    def calcular_distancia_km(self, lat_origen: float, lon_origen: float) -> float:
        radio_tierra_km = 6371.0
        d_lat = math.radians(self.latitud - lat_origen)
        d_lon = math.radians(self.longitud - lon_origen)
        lat1 = math.radians(lat_origen)
        lat2 = math.radians(self.latitud)

        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(radio_tierra_km * c, 2)

    # REGLA DE NEGOCIO: validar estado activo, categoría y radio
    def coincide_busqueda(
        self,
        lat_origen: float,
        lon_origen: float,
        radio_km: float,
        categoria: Optional[str] = None,
    ) -> tuple[bool, float]:
        if not self.activo:
            return False, 0.0
        if categoria and self.categoria != categoria.strip().upper():
            return False, 0.0
        distancia = self.calcular_distancia_km(lat_origen, lon_origen)
        if distancia > radio_km:
            return False, distancia
        return True, distancia

    def to_response(self, distancia_km: float) -> dict:
        return {
            "id_poi":   self.id_poi,
            "nombre":   self.nombre,
            "categoria": self.categoria,
            "ubicacion": {
                "type":        "Point",
                "coordinates": [round(self.longitud, 6), round(self.latitud, 6)],
            },
            "distancia_km":        round(float(distancia_km), 2),
            "calificacion_promedio": self.calificacion_promedio,
            "direccion":           self.direccion,
            "horario_apertura":    self.horario_apertura,
            "horario_cierre":      self.horario_cierre,
            "estado_operativo":    self.estado_operativo,
        }


# ── Excepciones de dominio (mapeadas a 400 y 503) ─────────────
class ValidacionNavegacionError(ValueError):
    """Error en parámetros de consulta de navegación/mapa (HTTP 400)."""


class ServicioCartografiaError(Exception):
    """Falla del motor/extensión geoespacial o timeout de BD (HTTP 503)."""