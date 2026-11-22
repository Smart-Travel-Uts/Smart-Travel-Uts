from typing import List, Optional
from domain.notificacion import (
    HistorialNotificacionesData,
    HistorialNotificacionesResponse,
    Notificacion,
    NotificacionRepositorioError,
)
from repository.notificacion_repository import NotificacionRepository


class NotificacionService:
    def __init__(self, repository: Optional[NotificacionRepository] = None) -> None:
        self._repository = repository or NotificacionRepository()

    def obtener_historial(self, usuario_id: str) -> HistorialNotificacionesResponse:
        try:
            notificaciones: List[Notificacion] = self._repository.obtener_por_usuario(
                usuario_id
            )
        except NotificacionRepositorioError as exc:
            raise NotificacionRepositorioError(
                "No fue posible obtener el historial de notificaciones"
            ) from exc

        notificaciones_ordenadas = sorted(
            notificaciones,
            key=lambda item: item.fecha_envio,
            reverse=True,
        )

        if not notificaciones_ordenadas:
            return HistorialNotificacionesResponse(
                message="No se encontraron notificaciones para el usuario",
                data=HistorialNotificacionesData(
                    total=0,
                    notificaciones=[],
                ),
                success=True,
            )

        return HistorialNotificacionesResponse(
            message="Consulta de notificaciones exitosa",
            data=HistorialNotificacionesData(
                total=len(notificaciones_ordenadas),
                notificaciones=notificaciones_ordenadas,
            ),
            success=True,
        )