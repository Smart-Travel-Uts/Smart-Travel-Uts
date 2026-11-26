# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _formatear_iso_utc(dt: datetime) -> str:
    dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parsear_fecha_iso(valor: str, nombre_campo: str) -> date:
    texto = str(valor).strip()
    try:
        return date.fromisoformat(texto[:10])
    except ValueError as exc:
        raise ValueError(
            f"Formato de fecha inválido en {nombre_campo}. Use YYYY-MM-DD"
        ) from exc


def _parsear_datetime_iso(valor: str, nombre_campo: str) -> datetime:
    texto = str(valor).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(texto)
    except ValueError as exc:
        raise ValueError(
            f"Formato ISO 8601 inválido en {nombre_campo}"
        ) from exc
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ── Schemas de ENTRADA (lo que recibe la API del cliente) ────
class PresupuestoEntrada(BaseModel):
    moneda: str   = Field("COP", min_length=2, max_length=10)
    monto:  float = Field(0.0, ge=0.0)

    # ── REGLA DE NEGOCIO: moneda normalizada en mayúsculas ──
    @field_validator("moneda")
    @classmethod
    def moneda_valida(cls, v: str) -> str:
        return v.strip().upper()

    # ── REGLA DE NEGOCIO: monto con dos decimales máximo ───
    @field_validator("monto")
    @classmethod
    def monto_valido(cls, v: float) -> float:
        return round(float(v), 2)


class ItinerarioCreate(BaseModel):
    titulo:               str                = Field(..., min_length=2, description="Título del itinerario")
    destino_principal:    str                = Field(..., min_length=2, description="Ciudad o destino base")
    fecha_inicio:         str                = Field(..., description="Fecha inicio YYYY-MM-DD")
    fecha_fin:            str                = Field(..., description="Fecha fin YYYY-MM-DD")
    presupuesto_estimado: PresupuestoEntrada = Field(default_factory=PresupuestoEntrada)

    # ── REGLA DE NEGOCIO: título y destino sin espacios vacíos ──
    @field_validator("titulo", "destino_principal")
    @classmethod
    def texto_limpio(cls, v: str) -> str:
        limpio = v.strip()
        if len(limpio) < 2:
            raise ValueError("El campo debe tener al menos 2 caracteres")
        return limpio

    # ── REGLA DE NEGOCIO: fechas en formato ISO YYYY-MM-DD ─
    @field_validator("fecha_inicio", "fecha_fin")
    @classmethod
    def validar_formato_fecha(cls, v: str, info) -> str:
        _parsear_fecha_iso(v, info.field_name)
        return v.strip()[:10]


class UbicacionActividadEntrada(BaseModel):
    nombre:      str         = Field(..., min_length=1)
    coordenadas: list[float] = Field(..., min_length=2, max_length=2)

    @field_validator("coordenadas")
    @classmethod
    def coordenadas_validas(cls, v: list[float]) -> list[float]:
        lon, lat = float(v[0]), float(v[1])
        if not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
            raise ValueError("Coordenadas fuera de rango WGS84 válido")
        return [round(lon, 4), round(lat, 4)]


class ActividadCreate(BaseModel):
    tipo:          str                            = Field(..., description="VUELO, ALOJAMIENTO, PUNTO_INTERES, TRANSPORTE_LOCAL, ACTIVIDAD_PERSONAL")
    referencia_id: Optional[str]                    = Field(None)
    titulo:        str                            = Field(..., min_length=2)
    hora_inicio:   str                            = Field(..., description="ISO 8601 UTC")
    hora_fin:      str                            = Field(..., description="ISO 8601 UTC")
    ubicacion:     Optional[UbicacionActividadEntrada] = None
    costo:         float                          = Field(0.0, ge=0.0)
    notas:         Optional[str]                    = Field("")

    # ── REGLA DE NEGOCIO: tipos de ítem permitidos ─────────
    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        limpio = v.strip().upper()
        permitidos = {
            "VUELO",
            "ALOJAMIENTO",
            "PUNTO_INTERES",
            "TRANSPORTE_LOCAL",
            "ACTIVIDAD_PERSONAL",
        }
        if limpio not in permitidos:
            raise ValueError(
                "Tipo de actividad inválido. Valores permitidos: VUELO, ALOJAMIENTO, PUNTO_INTERES, TRANSPORTE_LOCAL, ACTIVIDAD_PERSONAL"
            )
        return limpio

    @field_validator("titulo")
    @classmethod
    def titulo_valido(cls, v: str) -> str:
        limpio = v.strip()
        if len(limpio) < 2:
            raise ValueError("El título de la actividad debe tener al menos 2 caracteres")
        return limpio

    @field_validator("hora_inicio", "hora_fin")
    @classmethod
    def validar_horas_iso(cls, v: str, info) -> str:
        _parsear_datetime_iso(v, info.field_name)
        return v.strip()

    @field_validator("costo")
    @classmethod
    def costo_valido(cls, v: float) -> float:
        return round(float(v), 2)


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ────
class ItinerarioCreadoDataResponse(BaseModel):
    id_itinerario:     str
    id_usuario:        str
    titulo:            str
    destino_principal: str
    fecha_inicio:      str
    fecha_fin:         str
    estado:            str
    total_dias:        int
    fecha_creacion:    str


class ItinerarioCreadoResponse(BaseModel):
    message: str
    data:    ItinerarioCreadoDataResponse
    success: bool = True


class UbicacionActividadResponse(BaseModel):
    nombre:      str
    coordenadas: list[float]


class ActividadResponse(BaseModel):
    id_actividad:  str
    tipo:          str
    referencia_id: Optional[str] = None
    titulo:        str
    hora_inicio:   str
    hora_fin:      str
    ubicacion:     Optional[UbicacionActividadResponse] = None
    costo:         float
    notas:         str

    model_config = ConfigDict(from_attributes=True)


class DiaCronogramaResponse(BaseModel):
    dia_numero:  int
    fecha:       str
    actividades: list[ActividadResponse]


class ResumenCostosResponse(BaseModel):
    moneda:          str
    total_calculado: float


class ItinerarioDetalleDataResponse(BaseModel):
    id_itinerario:     str
    titulo:            str
    destino_principal: str
    fecha_inicio:      str
    fecha_fin:         str
    resumen_costos:    ResumenCostosResponse
    dias:              list[DiaCronogramaResponse]


class ItinerarioDetalleResponse(BaseModel):
    message: str
    data:    ItinerarioDetalleDataResponse
    success: bool = True


class ErrorItinerarioResponse(BaseModel):
    message: str
    data:    Optional[dict] = None
    success: bool = False


# ── Modelos internos del dominio (las "entidades reales") ──────
class ActividadItinerario:
    def __init__(
        self,
        id_actividad: str,
        tipo: str,
        titulo: str,
        hora_inicio: datetime,
        hora_fin: datetime,
        costo: float = 0.0,
        referencia_id: Optional[str] = None,
        ubicacion: Optional[dict] = None,
        notas: str = "",
    ):
        self.id_actividad  = id_actividad.strip().upper()
        self.tipo          = tipo.strip().upper()
        self.referencia_id = referencia_id.strip().upper() if referencia_id else None
        self.titulo        = titulo.strip()
        self.hora_inicio   = hora_inicio.astimezone(timezone.utc) if hora_inicio.tzinfo else hora_inicio.replace(tzinfo=timezone.utc)
        self.hora_fin      = hora_fin.astimezone(timezone.utc) if hora_fin.tzinfo else hora_fin.replace(tzinfo=timezone.utc)
        self.ubicacion     = ubicacion
        self.costo         = round(float(costo), 2)
        self.notas         = (notas or "").strip()

    # REGLA DE NEGOCIO: ¿solapa con otro rango horario?
    def solapa_con(self, otra_inicio: datetime, otra_fin: datetime) -> bool:
        ini_b = otra_inicio.astimezone(timezone.utc) if otra_inicio.tzinfo else otra_inicio.replace(tzinfo=timezone.utc)
        fin_b = otra_fin.astimezone(timezone.utc) if otra_fin.tzinfo else otra_fin.replace(tzinfo=timezone.utc)
        return self.hora_inicio < fin_b and self.hora_fin > ini_b

    def to_response(self) -> dict:
        return {
            "id_actividad":  self.id_actividad,
            "tipo":          self.tipo,
            "referencia_id": self.referencia_id,
            "titulo":        self.titulo,
            "hora_inicio":   _formatear_iso_utc(self.hora_inicio),
            "hora_fin":      _formatear_iso_utc(self.hora_fin),
            "ubicacion":     self.ubicacion,
            "costo":         self.costo,
            "notas":         self.notas,
        }


class Itinerario:
    def __init__(
        self,
        id_itinerario: str,
        id_usuario: str,
        titulo: str,
        destino_principal: str,
        fecha_inicio: date,
        fecha_fin: date,
        moneda: str = "COP",
        presupuesto_monto: float = 0.0,
        estado: str = "BORRADOR",
        fecha_creacion: Optional[datetime] = None,
        actividades: Optional[list[ActividadItinerario]] = None,
    ):
        self.id_itinerario     = id_itinerario.strip().upper()
        self.id_usuario        = id_usuario.strip().upper()
        self.titulo            = titulo.strip()
        self.destino_principal = destino_principal.strip()
        self.fecha_inicio      = fecha_inicio
        self.fecha_fin         = fecha_fin
        self.moneda            = moneda.strip().upper()
        self.presupuesto_monto = round(float(presupuesto_monto), 2)
        self.estado            = estado.strip().upper()
        self.fecha_creacion    = fecha_creacion or datetime.now(timezone.utc)
        self.actividades: list[ActividadItinerario] = list(actividades) if actividades else []

    @property
    def total_dias(self) -> int:
        return (self.fecha_fin - self.fecha_inicio).days + 1

    # REGLA DE NEGOCIO: ¿pertenece al usuario autenticado?
    def es_propietario(self, id_usuario: str) -> bool:
        return self.id_usuario == id_usuario.strip().upper()

    # REGLA DE NEGOCIO: validar rango de fechas y sin solapamientos antes de agregar
    def validar_y_agregar_actividad(self, actividad: ActividadItinerario) -> None:
        if not (self.fecha_inicio <= actividad.hora_inicio.date() <= self.fecha_fin) or not (
            self.fecha_inicio <= actividad.hora_fin.date() <= self.fecha_fin
        ):
            raise ValidacionItinerarioError(
                f"La actividad debe estar dentro del rango de fechas del itinerario ({self.fecha_inicio.isoformat()} a {self.fecha_fin.isoformat()})"
            )

        for existente in self.actividades:
            if existente.solapa_con(actividad.hora_inicio, actividad.hora_fin):
                raise ValidacionItinerarioError(
                    f"Solapamiento de horario con la actividad '{existente.titulo}' ({_formatear_iso_utc(existente.hora_inicio)} - {_formatear_iso_utc(existente.hora_fin)})"
                )

        self.actividades.append(actividad)

    def calcular_total_costos(self) -> float:
        return round(sum(act.costo for act in self.actividades), 2)

    def to_creado_response(self) -> dict:
        return {
            "id_itinerario":     self.id_itinerario,
            "id_usuario":        self.id_usuario,
            "titulo":            self.titulo,
            "destino_principal": self.destino_principal,
            "fecha_inicio":      self.fecha_inicio.isoformat(),
            "fecha_fin":         self.fecha_fin.isoformat(),
            "estado":            self.estado,
            "total_dias":        self.total_dias,
            "fecha_creacion":    _formatear_iso_utc(self.fecha_creacion),
        }

    def to_detalle_response(self) -> dict:
        dias_lista: list[dict] = []
        for idx in range(self.total_dias):
            fecha_actual = self.fecha_inicio + timedelta(days=idx)
            acts_dia = sorted(
                [a for a in self.actividades if a.hora_inicio.date() == fecha_actual],
                key=lambda a: a.hora_inicio,
            )
            dias_lista.append(
                {
                    "dia_numero":  idx + 1,
                    "fecha":       fecha_actual.isoformat(),
                    "actividades": [a.to_response() for a in acts_dia],
                }
            )

        return {
            "id_itinerario":     self.id_itinerario,
            "titulo":            self.titulo,
            "destino_principal": self.destino_principal,
            "fecha_inicio":      self.fecha_inicio.isoformat(),
            "fecha_fin":         self.fecha_fin.isoformat(),
            "resumen_costos": {
                "moneda":          self.moneda,
                "total_calculado": self.calcular_total_costos(),
            },
            "dias": dias_lista,
        }


# ── Excepciones de dominio (mapeadas a 400, 401, 403 y 404) ───
class AutenticacionItinerarioError(Exception):
    """Token JWT ausente o inválido (HTTP 401)."""


class AccesoDenegadoItinerarioError(Exception):
    """El usuario no es propietario del itinerario (HTTP 403)."""


class ItinerarioNoEncontradoError(Exception):
    """Itinerario o actividad no existe (HTTP 404)."""


class ValidacionItinerarioError(ValueError):
    """Error de validación o conflicto de horario (HTTP 400)."""