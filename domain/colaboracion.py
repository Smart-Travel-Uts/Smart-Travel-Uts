# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


ROLES_INVITACION = {"LECTOR", "EDITOR"}
ROLES_TODOS = {"PROPIETARIO", "EDITOR", "LECTOR"}


# ── Schema de ENTRADA (lo que recibe la API del cliente) ──────
class InvitacionItemCreate(BaseModel):
    email: str = Field(..., min_length=5, description="Correo electrónico del invitado")
    rol:   str = Field(..., description="Rol asignado: LECTOR o EDITOR")

    # ── REGLA DE NEGOCIO: correo válido con formato básico ────
    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        limpio = (v or "").strip().lower()
        if "@" not in limpio or "." not in limpio.split("@")[-1]:
            raise ValueError(f"Correo electrónico inválido: '{v}'")
        return limpio

    # ── REGLA DE NEGOCIO: rol de invitación válido ──────────
    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: str) -> str:
        rol_limpio = (v or "").strip().upper()
        if rol_limpio not in ROLES_INVITACION:
            raise ValueError("El rol de invitación debe ser LECTOR o EDITOR")
        return rol_limpio


class InvitarColaboradoresRequest(BaseModel):
    invitaciones:          list[InvitacionItemCreate] = Field(..., min_length=1)
    mensaje_personalizado: Optional[str]                = Field(None, max_length=500)


# ── Schemas de SALIDA (lo que devuelve la API al cliente) ──────
class ColaboradorAgregadoResponse(BaseModel):
    id_colaborador:    str
    email:             str
    rol:               str
    estado_invitacion: str
    fecha_invitacion:  str


class InvitarColaboradoresDataResponse(BaseModel):
    id_itinerario:           str
    titulo_viaje:            str
    colaboradores_agregados: list[ColaboradorAgregadoResponse]
    enlace_compartido:       str


class InvitarColaboradoresResponse(BaseModel):
    message: str
    data:    InvitarColaboradoresDataResponse
    success: bool = True


class ColaboradorDetalleResponse(BaseModel):
    id_colaborador:    str
    id_usuario:        Optional[str] = None
    email:             str
    rol:               str
    estado_invitacion: str
    fecha_invitacion:  str


class ListaColaboradoresDataResponse(BaseModel):
    id_itinerario: str
    total:         int
    colaboradores: list[ColaboradorDetalleResponse]


class ListaColaboradoresResponse(BaseModel):
    message: str
    data:    ListaColaboradoresDataResponse
    success: bool = True


class ErrorPermisoDataResponse(BaseModel):
    codigo_error: str
    detalles:     str


class ErrorPermisoResponse(BaseModel):
    message: str
    data:    ErrorPermisoDataResponse
    success: bool = False


# ── Modelo interno del dominio (las "entidades reales") ───────
class ColaboradorItinerario:
    def __init__(
        self,
        id_colaborador: str,
        email: str,
        rol: str,
        estado_invitacion: str = "PENDIENTE",
        id_usuario: Optional[str] = None,
        fecha_invitacion: Optional[datetime] = None,
    ):
        self.id_colaborador    = id_colaborador
        self.email             = email.strip().lower()
        self.rol               = rol.strip().upper()
        self.estado_invitacion = estado_invitacion.strip().upper()
        self.id_usuario        = id_usuario.strip().upper() if id_usuario else None
        self.fecha_invitacion  = fecha_invitacion or datetime.now(timezone.utc)

    # REGLA DE NEGOCIO: ¿tiene permiso de edición?
    def puede_editar(self) -> bool:
        return self.rol in {"PROPIETARIO", "EDITOR"} and self.estado_invitacion in {
            "ACEPTADA",
            "PENDIENTE",
            "ACTIVO",
        }

    def to_agregado_response(self) -> dict:
        return {
            "id_colaborador":    self.id_colaborador,
            "email":             self.email,
            "rol":               self.rol,
            "estado_invitacion": self.estado_invitacion,
            "fecha_invitacion":  self.fecha_invitacion.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    def to_detalle_response(self) -> dict:
        base = self.to_agregado_response()
        base["id_usuario"] = self.id_usuario
        return base


class EnlaceCompartido:
    def __init__(
        self,
        token: str,
        id_itinerario: str,
        creado_por: str,
        expira_en: Optional[datetime] = None,
        activo: bool = True,
    ):
        self.token         = token
        self.id_itinerario = id_itinerario
        self.creado_por    = creado_por.strip().upper()
        self.expira_en     = expira_en or (datetime.now(timezone.utc) + timedelta(days=7))
        self.activo        = activo

    # REGLA DE NEGOCIO: verificar si el enlace está vigente y no expiró
    def esta_vigente(self, ahora: Optional[datetime] = None) -> bool:
        referencia = ahora or datetime.now(timezone.utc)
        return self.activo and referencia < self.expira_en

    def to_url(self) -> str:
        return f"https://smarttravel.app/i/shared?token={self.token}"


class RegistroAuditoria:
    def __init__(
        self,
        id_auditoria: str,
        id_itinerario: str,
        id_usuario: str,
        rol_usuario: str,
        accion: str,
        detalle: str,
        version_resultante: int,
        fecha_hora_utc: Optional[datetime] = None,
    ):
        self.id_auditoria       = id_auditoria
        self.id_itinerario      = id_itinerario
        self.id_usuario         = id_usuario
        self.rol_usuario        = rol_usuario
        self.accion             = accion
        self.detalle            = detalle
        self.version_resultante = version_resultante
        self.fecha_hora_utc     = fecha_hora_utc or datetime.now(timezone.utc)

    def to_response(self) -> dict:
        return {
            "id_auditoria":       self.id_auditoria,
            "id_itinerario":      self.id_itinerario,
            "id_usuario":         self.id_usuario,
            "rol_usuario":        self.rol_usuario,
            "accion":             self.accion,
            "detalle":            self.detalle,
            "version_resultante": self.version_resultante,
            "fecha_hora_utc":     self.fecha_hora_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }