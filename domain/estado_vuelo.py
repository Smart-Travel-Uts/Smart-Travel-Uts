import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

ID_VUELO_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
ESTADOS_OPERATIVOS_VALIDOS = {"A TIEMPO", "RETRASADO", "CANCELADO", "EMBARCANDO", "DESCONOCIDO"}


# ── Schema de ENTRADA / VALIDACIÓN (parámetro id_vuelo) ───────
class EstadoVueloConsultaRequest(BaseModel):
    id_vuelo: str = Field(..., min_length=3, max_length=20, description="Identificador del vuelo")

    # ── REGLA DE NEGOCIO: formato válido de id_vuelo ──────────
    @field_validator("id_vuelo")
    @classmethod
    def validar_formato_id_vuelo(cls, v: str) -> str:
        limpio = v.strip().upper()
        if not ID_VUELO_REGEX.match(limpio):
            raise ValueError("El formato del identificador de vuelo (id_vuelo) no es válido")
        return limpio


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ────
class EstadoVueloDataResponse(BaseModel):
    id_vuelo: str
    aerolinea: str
    numero_vuelo: str
    origen: str
    destino: str
    estado_actual: str
    hora_salida_programada: str
    hora_salida_estimada: str
    puerta: str
    observaciones: str

    model_config = ConfigDict(from_attributes=True)


class ConsultaEstadoVueloResponse(BaseModel):
    message: str
    data: Optional[EstadoVueloDataResponse] = None
    success: bool = True


class VueloNoEncontradoDataResponse(BaseModel):
    id_vuelo: str
    estado_actual: str = "DESCONOCIDO"


class VueloNoEncontradoResponse(BaseModel):
    mensaje: str
    data: VueloNoEncontradoDataResponse
    success: bool = False


# ── Modelo interno del dominio (la "entidad real") ────────────
class EstadoVuelo:
    def __init__(
        self,
        id_vuelo: str,
        aerolinea: str,
        numero_vuelo: str,
        origen: str,
        destino: str,
        estado_actual: str,
        hora_salida_programada: str,
        hora_salida_estimada: str,
        puerta: str,
        observaciones: str,
    ) -> None:
        self.id_vuelo = id_vuelo.strip().upper()
        self.aerolinea = aerolinea.strip()
        self.numero_vuelo = numero_vuelo.strip().upper()
        self.origen = origen.strip().upper()
        self.destino = destino.strip().upper()
        self.estado_actual = estado_actual.strip().upper()
        self.hora_salida_programada = hora_salida_programada
        self.hora_salida_estimada = hora_salida_estimada
        self.puerta = puerta.strip().upper()
        self.observaciones = observaciones.strip()

    # REGLA DE NEGOCIO: ¿el vuelo presenta retraso?
    def esta_retrasado(self) -> bool:
        return self.estado_actual == "RETRASADO"

    # REGLA DE NEGOCIO: ¿el vuelo fue cancelado?
    def esta_cancelado(self) -> bool:
        return self.estado_actual == "CANCELADO"

    # REGLA DE NEGOCIO: actualizar estado y hora estimada de salida
    def actualizar_estado(
        self,
        nuevo_estado: str,
        nueva_hora_estimada: Optional[str] = None,
        nueva_puerta: Optional[str] = None,
        observacion: Optional[str] = None,
    ) -> None:
        estado_limpio = nuevo_estado.strip().upper()
        if estado_limpio not in ESTADOS_OPERATIVOS_VALIDOS:
            raise ValueError(f"Estado operativo '{nuevo_estado}' no es válido")
        self.estado_actual = estado_limpio
        if nueva_hora_estimada:
            self.hora_salida_estimada = nueva_hora_estimada
        if nueva_puerta:
            self.puerta = nueva_puerta.strip().upper()
        if observacion:
            self.observaciones = observacion.strip()

    def to_response(self) -> dict:
        return {
            "id_vuelo": self.id_vuelo,
            "aerolinea": self.aerolinea,
            "numero_vuelo": self.numero_vuelo,
            "origen": self.origen,
            "destino": self.destino,
            "estado_actual": self.estado_actual,
            "hora_salida_programada": self.hora_salida_programada,
            "hora_salida_estimada": self.hora_salida_estimada,
            "puerta": self.puerta,
            "observaciones": self.observaciones,
        }


# ── Excepciones de dominio (mapeadas a 400 / 404 / 503) ───────
class ValidacionEstadoVueloError(ValueError):
    """Error de validación en el identificador de vuelo (HTTP 400)."""


class VueloNoEncontradoError(Exception):
    """Error cuando el vuelo no existe o no está registrado (HTTP 404)."""


class ProveedorEstadoVueloError(Exception):
    """Error de comunicación con proveedor o BD de aeropuertos (HTTP 503)."""