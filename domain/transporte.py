# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

import math
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TIPOS_TRANSPORTE_QUERY = Literal[
    "AUTOBUS_RAPIDO",
    "METRO",
    "TRANVIA",
    "TODOS",
]


def _formatear_iso_utc(dt: datetime) -> str:
    dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parsear_hora_salida(valor: Optional[str]) -> datetime:
    if valor is None:
        return datetime.now(timezone.utc)
    texto = str(valor).strip()
    if not texto:
        return datetime.now(timezone.utc)
    normalizada = texto.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalizada)
    except ValueError as exc:
        raise ValueError(
            "Formato ISO 8601 incorrecto en el parámetro hora_salida"
        ) from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# ── Schema de ENTRADA (lo que recibe la API del cliente) ──────
class BusquedaRutasQuery(BaseModel):
    latitud_origen:   float          = Field(..., description="Latitud WGS84 de salida [-90.0, 90.0]")
    longitud_origen:  float          = Field(..., description="Longitud WGS84 de salida [-180.0, 180.0]")
    latitud_destino:  float          = Field(..., description="Latitud WGS84 de llegada [-90.0, 90.0]")
    longitud_destino: float          = Field(..., description="Longitud WGS84 de llegada [-180.0, 180.0]")
    hora_salida:      Optional[str]  = Field(None, description="Hora programada en formato ISO 8601")
    tipo_transporte:  Optional[str]  = Field(None, description="AUTOBUS_RAPIDO, METRO, TRANVIA, TODOS")

    # ── REGLA DE NEGOCIO: latitud entre -90.0 y 90.0 ────────
    @field_validator("latitud_origen", "latitud_destino")
    @classmethod
    def latitud_valida(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("La latitud debe estar dentro del rango [-90.0, 90.0]")
        return round(float(v), 6)

    # ── REGLA DE NEGOCIO: longitud entre -180.0 y 180.0 ─────
    @field_validator("longitud_origen", "longitud_destino")
    @classmethod
    def longitud_valida(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("La longitud debe estar dentro del rango [-180.0, 180.0]")
        return round(float(v), 6)

    # ── REGLA DE NEGOCIO: validar hora_salida ISO 8601 ──────
    @field_validator("hora_salida", mode="before")
    @classmethod
    def hora_salida_valida(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        _parsear_hora_salida(str(v))
        return str(v).strip()

    # ── REGLA DE NEGOCIO: validar tipo_transporte ───────────
    @field_validator("tipo_transporte", mode="before")
    @classmethod
    def tipo_transporte_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        limpio = str(v).strip().upper()
        if not limpio:
            return None
        permitidos = {"AUTOBUS_RAPIDO", "METRO", "TRANVIA", "TODOS"}
        if limpio not in permitidos:
            raise ValueError(
                "Tipo de transporte inválido. Valores permitidos: AUTOBUS_RAPIDO, METRO, TRANVIA, TODOS"
            )
        return limpio

    # ── REGLA DE NEGOCIO: origen y destino no idénticos ────
    @model_validator(mode="after")
    def origen_distinto_destino(self) -> "BusquedaRutasQuery":
        if (
            round(self.latitud_origen, 6) == round(self.latitud_destino, 6)
            and round(self.longitud_origen, 6) == round(self.longitud_destino, 6)
        ):
            raise ValueError("Las coordenadas de origen y destino no pueden ser idénticas")
        return self

    def obtener_hora_salida_dt(self) -> datetime:
        return _parsear_hora_salida(self.hora_salida)


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ────
class PuntoGeolocalizadoResponse(BaseModel):
    latitud:           float
    longitud:          float
    direccion_cercana: str


class CostoTarifaResponse(BaseModel):
    moneda: str
    monto:  float


class ParadaIntermediaResponse(BaseModel):
    orden:                 int
    nombre_parada:         str
    coordenadas:           list[float]
    hora_estimada_llegada: str


class OpcionRutaResponse(BaseModel):
    id_ruta:                   str
    nombre_linea:              str
    tipo_transporte:           str
    duracion_estimada_minutos: int
    distancia_total_km:        float
    costo_tarifa:              CostoTarifaResponse
    frecuencia_minutos:        int
    proxima_salida:            str
    paradas_intermedias:       list[ParadaIntermediaResponse]
    estado_servicio:           str

    model_config = ConfigDict(from_attributes=True)


class RutasTransporteDataResponse(BaseModel):
    origen:         PuntoGeolocalizadoResponse
    destino:        PuntoGeolocalizadoResponse
    total_opciones: int
    opciones_ruta:  list[OpcionRutaResponse]


class RutasTransporteResponse(BaseModel):
    message: str
    data:    RutasTransporteDataResponse
    success: bool = True


class ErrorTransporteDataResponse(BaseModel):
    errores: list[str]


class ErrorTransporteResponse(BaseModel):
    message: str
    data:    ErrorTransporteDataResponse
    success: bool = False


# ── Modelo interno del dominio (la "entidad real") ────────────
class RutaUrbana:
    def __init__(
        self,
        id_ruta: str,
        nombre_linea: str,
        tipo_transporte: str,
        lat_inicio: float,
        lon_inicio: float,
        lat_fin: float,
        lon_fin: float,
        duracion_estimada_minutos: int,
        distancia_total_km: float,
        tarifa_monto: float,
        frecuencia_minutos: int,
        paradas_plantilla: list[dict],
        estado_servicio: str = "NORMAL",
        moneda: str = "COP",
        activa: bool = True,
    ):
        self.id_ruta                   = id_ruta.strip().upper()
        self.nombre_linea              = nombre_linea.strip()
        self.tipo_transporte           = tipo_transporte.strip().upper()
        self.lat_inicio                = float(lat_inicio)
        self.lon_inicio                = float(lon_inicio)
        self.lat_fin                   = float(lat_fin)
        self.lon_fin                   = float(lon_fin)
        self.duracion_estimada_minutos = int(duracion_estimada_minutos)
        self.distancia_total_km        = round(float(distancia_total_km), 1)
        self.tarifa_monto              = round(float(tarifa_monto), 2)
        self.frecuencia_minutos        = int(frecuencia_minutos)
        self.paradas_plantilla         = paradas_plantilla
        self.estado_servicio           = estado_servicio.strip().upper()
        self.moneda                    = moneda.strip().upper()
        self.activa                    = bool(activa)

    def _distancia_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2.0) ** 2
        )
        return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    # REGLA DE NEGOCIO: ¿cubre origen y destino dentro del radio y modo solicitado?
    def cubre_trayecto(
        self,
        lat_origen: float,
        lon_origen: float,
        lat_destino: float,
        lon_destino: float,
        tipo_transporte: Optional[str] = None,
        radio_cobertura_km: float = 3.5,
    ) -> bool:
        if not self.activa:
            return False
        if tipo_transporte and tipo_transporte != "TODOS":
            if self.tipo_transporte != tipo_transporte.strip().upper():
                return False

        dist_origen = self._distancia_km(lat_origen, lon_origen, self.lat_inicio, self.lon_inicio)
        dist_destino = self._distancia_km(lat_destino, lon_destino, self.lat_fin, self.lon_fin)
        dist_origen_a_fin = self._distancia_km(lat_origen, lon_origen, self.lat_fin, self.lon_fin)
        if dist_origen_a_fin < dist_origen and dist_origen > 1.2:
            return False

        return dist_origen <= radio_cobertura_km and dist_destino <= radio_cobertura_km

    # REGLA DE NEGOCIO: calcular próxima salida y horas estimadas de paradas
    def to_response(self, hora_salida_dt: datetime) -> dict:
        proxima = hora_salida_dt + timedelta(minutes=min(5, self.frecuencia_minutos // 2))
        paradas_calculadas: list[dict] = []
        for idx, parada in enumerate(self.paradas_plantilla, start=1):
            minutos_offset = int(parada.get("offset_minutos", idx * 4))
            llegada = proxima + timedelta(minutes=minutos_offset)
            paradas_calculadas.append(
                {
                    "orden": idx,
                    "nombre_parada": parada["nombre_parada"],
                    "coordenadas": [
                        round(float(parada["longitud"]), 4),
                        round(float(parada["latitud"]), 4),
                    ],
                    "hora_estimada_llegada": _formatear_iso_utc(llegada),
                }
            )

        return {
            "id_ruta":                   self.id_ruta,
            "nombre_linea":              self.nombre_linea,
            "tipo_transporte":           self.tipo_transporte,
            "duracion_estimada_minutos": self.duracion_estimada_minutos,
            "distancia_total_km":        self.distancia_total_km,
            "costo_tarifa": {
                "moneda": self.moneda,
                "monto":  self.tarifa_monto,
            },
            "frecuencia_minutos":        self.frecuencia_minutos,
            "proxima_salida":            _formatear_iso_utc(proxima),
            "paradas_intermedias":       paradas_calculadas,
            "estado_servicio":           self.estado_servicio,
        }


# ── Excepciones de dominio (mapeadas a 400 y 503) ─────────────
class ValidacionTransporteError(ValueError):
    """Error en parámetros de geolocalización o itinerario (HTTP 400)."""


class ServicioRuteoError(Exception):
    """Falla o timeout del motor de ruteo GTFS / base de datos espacial (HTTP 503)."""