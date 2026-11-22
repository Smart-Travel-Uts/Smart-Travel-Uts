from typing import Dict, List
from domain.notificacion import Notificacion, NotificacionRepositorioError


class NotificacionRepository:
    def __init__(self) -> None:
        self._notificaciones_por_usuario: Dict[str, List[Notificacion]] = {
            "usr-001": [
                Notificacion(
                    notificacion_id="NOT-8812",
                    tipo="ALERTA_VUELO",
                    titulo="Cambio de puerta de embarque",
                    mensaje="Su vuelo AV9301 cambió a la puerta 4B.",
                    fecha_envio="2026-10-25T14:30:00Z",
                    leido=False,
                ),
                Notificacion(
                    notificacion_id="NOT-8805",
                    tipo="CONFIRMACION_RESERVA",
                    titulo="Reserva confirmada",
                    mensaje="Tu reserva de hotel en Cartagena está confirmada.",
                    fecha_envio="2026-10-24T09:15:00Z",
                    leido=True,
                ),
            ],
            "usr-sin-notificaciones": [],
        }
        self._simular_fallo: bool = False

    def configurar_fallo(self, simular_fallo: bool) -> None:
        """Permite simular un fallo de almacenamiento en pruebas (Caso 4 -> 503)."""
        self._simular_fallo = simular_fallo

    def obtener_por_usuario(self, usuario_id: str) -> List[Notificacion]:
        if self._simular_fallo:
            raise NotificacionRepositorioError(
                "No fue posible obtener el historial de notificaciones"
            )
        try:
            items = self._notificaciones_por_usuario.get(usuario_id, [])
            return [item.model_copy() for item in items]
        except NotificacionRepositorioError:
            raise
        except Exception as exc:
            raise NotificacionRepositorioError(
                "No fue posible obtener el historial de notificaciones"
            ) from exc