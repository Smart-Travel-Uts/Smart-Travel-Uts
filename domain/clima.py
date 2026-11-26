# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Schema de ENTRADA (lo que recibe la API del cliente) ──────
class ConsultaClimaQuery(BaseModel):
    latitud:    Optional[float] = Field(None, description="Latitud WGS84 [-90.0, 90.0]")
    longitud:   Optional[float] = Field(None, description="Longitud WGS84 [-180.0, 180.0]")
    id_destino: Optional[str]   = Field(None, description="ID del destino, ej. DEST-BGA")
    dias:       int             = Field(3,    ge=1, le=7, description="Días de pronóstico (1 a 7)")
    unidades:   str             = Field("CELSIUS", description="CELSIUS o FAHRENHEIT")

    # ── REGLA DE NEGOCIO: normalizar unidades a mayúsculas ───
    @field_validator("unidades")
    @classmethod
    def unidades_validas(cls, v: str) -> str:
        limpia = (v or "CELSIUS").strip().upper()
        if limpia not in {"CELSIUS", "FAHRENHEIT"}:
            raise ValueError("Unidades inválidas. Use CELSIUS o FAHRENHEIT")
        return limpia

    # ── REGLA DE NEGOCIO: limpiar id_destino si se envía ──────
    @field_validator("id_destino")
    @classmethod
    def id_destino_limpio(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        limpio = v.strip().upper()
        return limpio if limpio else None


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ─────
class CoordenadasResponse(BaseModel):
    latitud:  float
    longitud: float


class DestinoClimaResponse(BaseModel):
    nombre:      str
    coordenadas: CoordenadasResponse


class ClimaActualResponse(BaseModel):
    fecha_hora_utc:          str
    temperatura_celsius:     float
    sensacion_termica_celsius: float
    condicion:               str
    descripcion:             str
    humedad_porcentaje:      int
    velocidad_viento_kmh:    float
    indice_uv:               int


class AlertaLocalResponse(BaseModel):
    id_alerta:        str
    tipo:             str
    nivel_riesgo:     str
    titulo:           str
    descripcion:      str
    emitido_por:      str
    fecha_emision:    str
    fecha_expiracion: str


class PronosticoDiaResponse(BaseModel):
    fecha:                             str
    temperatura_max_celsius:           float
    temperatura_min_celsius:           float
    probabilidad_precipitacion_porcentaje: int
    condicion_principal:               str


class PronosticoDataResponse(BaseModel):
    destino:         DestinoClimaResponse
    clima_actual:    ClimaActualResponse
    alertas_activas: list[AlertaLocalResponse]
    pronostico_dias: list[PronosticoDiaResponse]
    dato_obsoleto:   Optional[bool] = None


class PronosticoResponse(BaseModel):
    message: str
    data:    PronosticoDataResponse
    success: bool = True


class ErrorClimaDataResponse(BaseModel):
    errores: list[str]


class ErrorClimaResponse(BaseModel):
    message: str
    data:    Optional[ErrorClimaDataResponse] = None
    success: bool = False


# ── Modelo interno del dominio (las "entidades reales") ───────
class AlertaLocal:
    NIVELES_VALIDOS = {"INFORMATIVA", "ADVERTENCIA", "PELIGRO"}

    def __init__(
        self,
        id_alerta: str,
        tipo: str,
        nivel_riesgo: str,
        titulo: str,
        descripcion: str,
        emitido_por: str,
        fecha_emision: str,
        fecha_expiracion: str,
    ):
        nivel = nivel_riesgo.strip().upper()
        if nivel not in self.NIVELES_VALIDOS:
            raise ValueError(f"Nivel de riesgo inválido: {nivel_riesgo}")

        self.id_alerta        = id_alerta.strip().upper()
        self.tipo             = tipo.strip().upper()
        self.nivel_riesgo     = nivel
        self.titulo           = titulo.strip()
        self.descripcion      = descripcion.strip()
        self.emitido_por      = emitido_por.strip()
        self.fecha_emision    = fecha_emision
        self.fecha_expiracion = fecha_expiracion

    # REGLA DE NEGOCIO: ¿es una alerta de alto riesgo?
    def es_critica(self) -> bool:
        return self.nivel_riesgo == "PELIGRO"

    def to_response(self) -> dict:
        return {
            "id_alerta":        self.id_alerta,
            "tipo":             self.tipo,
            "nivel_riesgo":     self.nivel_riesgo,
            "titulo":           self.titulo,
            "descripcion":      self.descripcion,
            "emitido_por":      self.emitido_por,
            "fecha_emision":    self.fecha_emision,
            "fecha_expiracion": self.fecha_expiracion,
        }


class PronosticoDestino:
    def __init__(
        self,
        nombre_destino: str,
        latitud: float,
        longitud: float,
        clima_actual: dict,
        alertas_activas: list[AlertaLocal],
        pronostico_dias: list[dict],
        actualizado_en: Optional[datetime] = None,
    ):
        self.nombre_destino  = nombre_destino.strip()
        self.latitud         = round(float(latitud), 4)
        self.longitud        = round(float(longitud), 4)
        self.clima_actual    = clima_actual
        self.alertas_activas = list(alertas_activas)
        self.pronostico_dias = list(pronostico_dias)
        self.actualizado_en  = actualizado_en or datetime.now(timezone.utc)

    # REGLA DE NEGOCIO: convertir °C a °F si el cliente pide FAHRENHEIT
    @staticmethod
    def celsius_a_fahrenheit(celsius: float) -> float:
        return round((float(celsius) * 9 / 5) + 32, 1)

    # REGLA DE NEGOCIO: recortar pronóstico a la cantidad de días solicitada (1..7)
    def pronostico_por_dias(self, dias: int, unidades: str = "CELSIUS") -> list[dict]:
        limite = max(1, min(7, int(dias)))
        resultado: list[dict] = []

        for dia in self.pronostico_dias[:limite]:
            t_max = dia["temperatura_max_celsius"]
            t_min = dia["temperatura_min_celsius"]
            if unidades.upper() == "FAHRENHEIT":
                t_max = self.celsius_a_fahrenheit(t_max)
                t_min = self.celsius_a_fahrenheit(t_min)

            resultado.append(
                {
                    "fecha":                                 dia["fecha"],
                    "temperatura_max_celsius":               t_max,
                    "temperatura_min_celsius":               t_min,
                    "probabilidad_precipitacion_porcentaje": dia["probabilidad_precipitacion_porcentaje"],
                    "condicion_principal":                   dia["condicion_principal"],
                }
            )
        return resultado

    def to_response(
        self,
        dias: int = 3,
        unidades: str = "CELSIUS",
        dato_obsoleto: Optional[bool] = None,
    ) -> dict:
        actual = dict(self.clima_actual)
        if unidades.upper() == "FAHRENHEIT":
            actual["temperatura_celsius"] = self.celsius_a_fahrenheit(
                actual["temperatura_celsius"]
            )
            actual["sensacion_termica_celsius"] = self.celsius_a_fahrenheit(
                actual["sensacion_termica_celsius"]
            )

        data: dict = {
            "destino": {
                "nombre": self.nombre_destino,
                "coordenadas": {
                    "latitud":  self.latitud,
                    "longitud": self.longitud,
                },
            },
            "clima_actual":    actual,
            "alertas_activas": [a.to_response() for a in self.alertas_activas],
            "pronostico_dias": self.pronostico_por_dias(dias=dias, unidades=unidades),
        }
        if dato_obsoleto is not None:
            data["dato_obsoleto"] = dato_obsoleto
        return data