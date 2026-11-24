# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

COMISION_HOSPEDAJE_PORCENTAJE = 10.0
IMPUESTO_HOSPEDAJE_PORCENTAJE = 19.0


# ── Schemas de ENTRADA (lo que recibe/valida la API) ─────────
class BusquedaHospedajeQuery(BaseModel):
    destino:          str             = Field(..., min_length=2, description="Ciudad o destino")
    fecha_entrada:    date            = Field(..., description="Fecha de entrada (YYYY-MM-DD)")
    fecha_salida:     date            = Field(..., description="Fecha de salida (YYYY-MM-DD)")
    huespedes:        int             = Field(1, ge=1, description="Número de huéspedes (>= 1)")
    precio_min:       Optional[float] = Field(None, ge=0, description="Precio base por noche mínimo")
    precio_max:       Optional[float] = Field(None, ge=0, description="Precio base por noche máximo")
    calificacion_min: Optional[float] = Field(None, ge=0, le=5, description="Calificación mínima")

    # ── REGLA DE NEGOCIO: destino no vacío y limpio ──────────
    @field_validator("destino")
    @classmethod
    def destino_valido(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("El destino no puede estar vacío.")
        return limpio

    # ── REGLA DE NEGOCIO: precios con dos decimales máximo ────
    @field_validator("precio_min", "precio_max")
    @classmethod
    def precio_valido(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        return round(v, 2)

    # ── REGLA DE NEGOCIO: fecha_salida posterior a fecha_entrada
    @model_validator(mode="after")
    def fechas_y_rango_validos(self) -> "BusquedaHospedajeQuery":
        if self.fecha_salida <= self.fecha_entrada:
            raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
        if self.precio_min is not None and self.precio_max is not None and self.precio_max < self.precio_min:
            raise ValueError("El precio máximo no puede ser menor al precio mínimo.")
        return self


class DisponibilidadHospedajeQuery(BaseModel):
    fecha_entrada: date = Field(..., description="Fecha de entrada (YYYY-MM-DD)")
    fecha_salida:  date = Field(..., description="Fecha de salida (YYYY-MM-DD)")
    huespedes:     int  = Field(..., ge=1, description="Número de huéspedes (>= 1)")

    # ── REGLA DE NEGOCIO: fecha_salida posterior a fecha_entrada
    @model_validator(mode="after")
    def fechas_validas(self) -> "DisponibilidadHospedajeQuery":
        if self.fecha_salida <= self.fecha_entrada:
            raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
        return self


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ────
class AlojamientoResumenResponse(BaseModel):
    id_alojamiento:      str
    nombre:              str
    tipo_alojamiento:    str
    ciudad:              str
    calificacion_promedio: float
    precio_noche_base:   float
    moneda:              str
    servicios_destacados: list[str]

    model_config = ConfigDict(from_attributes=True)


class BusquedaHospedajeDataResponse(BaseModel):
    total_resultados: int
    alojamientos:     list[AlojamientoResumenResponse]


class BusquedaHospedajeResponse(BaseModel):
    message: str
    data:    BusquedaHospedajeDataResponse
    success: bool = True


class DesgloseTarifaResponse(BaseModel):
    subtotal_estancia:              float
    comision_plataforma_porcentaje: float
    monto_comision:                 float
    impuestos_cargos:               float
    precio_total:                   float
    moneda:                         str


class PoliticasAlojamientoResponse(BaseModel):
    check_in:      str
    check_out:     str
    cancelacion:   str
    restricciones: list[str]


class DisponibilidadDataResponse(BaseModel):
    id_alojamiento: str
    nombre:         str
    disponible:     bool
    noches:         int
    huespedes:      int
    desglose_tarifa: DesgloseTarifaResponse
    politicas:      PoliticasAlojamientoResponse


class DisponibilidadHospedajeResponse(BaseModel):
    message: str
    data:    DisponibilidadDataResponse
    success: bool = True


class ErrorHospedajeDataResponse(BaseModel):
    errores: list[str]


class ErrorHospedajeResponse(BaseModel):
    message: str
    data:    ErrorHospedajeDataResponse
    success: bool = False


# ── Modelo interno del dominio (la "entidad real") ────────────
class Alojamiento:
    def __init__(
        self,
        id_alojamiento: str,
        nombre: str,
        tipo_alojamiento: str,
        ciudad: str,
        calificacion_promedio: float,
        precio_noche_base: float,
        moneda: str,
        servicios_destacados: list[str],
        capacidad_maxima: int,
        cupo_disponible: bool,
        check_in: str,
        check_out: str,
        cancelacion: str,
        restricciones: list[str],
    ) -> None:
        self.id_alojamiento       = id_alojamiento.strip().upper()
        self.nombre               = nombre.strip()
        self.tipo_alojamiento     = tipo_alojamiento.strip().upper()
        self.ciudad               = ciudad.strip()
        self.calificacion_promedio = round(float(calificacion_promedio), 2)
        self.precio_noche_base    = round(float(precio_noche_base), 2)
        self.moneda               = moneda.strip().upper()
        self.servicios_destacados = list(servicios_destacados)
        self.capacidad_maxima     = int(capacidad_maxima)
        self.cupo_disponible      = bool(cupo_disponible)
        self.check_in             = check_in
        self.check_out            = check_out
        self.cancelacion          = cancelacion
        self.restricciones        = list(restricciones)

    # REGLA DE NEGOCIO: ¿hay cupo suficiente para los huéspedes?
    def tiene_cupo(self, huespedes: int = 1) -> bool:
        return self.cupo_disponible and self.capacidad_maxima >= huespedes

    # REGLA DE NEGOCIO: ¿cumple con filtros de búsqueda?
    def coincide_busqueda(
        self,
        destino: str,
        huespedes: int,
        precio_min: Optional[float] = None,
        precio_max: Optional[float] = None,
        calificacion_min: Optional[float] = None,
    ) -> bool:
        if destino.strip().lower() not in self.ciudad.lower():
            return False
        if not self.tiene_cupo(huespedes):
            return False
        if precio_min is not None and self.precio_noche_base < precio_min:
            return False
        if precio_max is not None and self.precio_noche_base > precio_max:
            return False
        if calificacion_min is not None and self.calificacion_promedio < calificacion_min:
            return False
        return True

    # REGLA DE NEGOCIO: calcular tarifa con 10% de comisión de plataforma
    def calcular_tarifa(self, noches: int, huespedes: int) -> dict:
        if noches <= 0:
            raise ValueError("La cantidad de noches debe ser mayor a 0.")
        if huespedes <= 0:
            raise ValueError("El número de huéspedes debe ser mayor a 0.")

        subtotal = round(self.precio_noche_base * noches, 2)
        comision = round(subtotal * (COMISION_HOSPEDAJE_PORCENTAJE / 100.0), 2)
        impuestos = round(subtotal * (IMPUESTO_HOSPEDAJE_PORCENTAJE / 100.0), 2)
        total = round(subtotal + comision + impuestos, 2)

        return {
            "subtotal_estancia":              subtotal,
            "comision_plataforma_porcentaje": COMISION_HOSPEDAJE_PORCENTAJE,
            "monto_comision":                 comision,
            "impuestos_cargos":               impuestos,
            "precio_total":                   total,
            "moneda":                         self.moneda,
        }

    def to_response(self) -> dict:
        return {
            "id_alojamiento":       self.id_alojamiento,
            "nombre":               self.nombre,
            "tipo_alojamiento":     self.tipo_alojamiento,
            "ciudad":               self.ciudad,
            "calificacion_promedio": self.calificacion_promedio,
            "precio_noche_base":    self.precio_noche_base,
            "moneda":               self.moneda,
            "servicios_destacados": self.servicios_destacados,
        }

    def to_disponibilidad_response(self, fecha_entrada: date, fecha_salida: date, huespedes: int) -> dict:
        noches = (fecha_salida - fecha_entrada).days
        return {
            "id_alojamiento": self.id_alojamiento,
            "nombre":          self.nombre,
            "disponible":      self.tiene_cupo(huespedes) and noches > 0,
            "noches":          noches,
            "huespedes":       huespedes,
            "desglose_tarifa": self.calcular_tarifa(noches=noches, huespedes=huespedes),
            "politicas": {
                "check_in":      self.check_in,
                "check_out":     self.check_out,
                "cancelacion":   self.cancelacion,
                "restricciones": self.restricciones,
            },
        }


# ── Excepciones de dominio (mapeadas a 400 / 404 / 503) ───────
class ValidacionHospedajeError(ValueError):
    """Error en parámetros de consulta o validación de hospedaje (HTTP 400)."""


class AlojamientoNoEncontradoError(Exception):
    """Error cuando el alojamiento no existe o no tiene disponibilidad (HTTP 404)."""


class ProveedorHospedajeError(Exception):
    """Error de comunicación con proveedor externo o BD de alojamientos (HTTP 503)."""