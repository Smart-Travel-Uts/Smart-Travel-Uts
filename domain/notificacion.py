from typing import List
from pydantic import BaseModel, Field


class Notificacion(BaseModel):
    notificacion_id: str = Field(..., min_length=1)
    tipo: str = Field(..., min_length=1)
    titulo: str = Field(..., min_length=1)
    mensaje: str = Field(..., min_length=1)
    fecha_envio: str = Field(..., min_length=1)
    leido: bool


class HistorialNotificacionesData(BaseModel):
    total: int = Field(..., ge=0)
    notificaciones: List[Notificacion] = Field(default_factory=list)


class HistorialNotificacionesResponse(BaseModel):
    message: str
    data: HistorialNotificacionesData
    success: bool


class NotificacionError(Exception):
    """Excepción base del dominio de notificaciones."""


class NotificacionRepositorioError(NotificacionError):
    """Error al consultar o acceder al almacenamiento de notificaciones."""


class NotificacionNoAutenticadoError(NotificacionError):
    """Error cuando la solicitud de notificaciones no está autenticada."""