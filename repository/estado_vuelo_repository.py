# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from domain.estado_vuelo import EstadoVuelo, ProveedorEstadoVueloError


class EstadoVueloRepository:

    def __init__(self) -> None:
        # Almacén en memoria: lista de objetos EstadoVuelo
        self._datos: list[EstadoVuelo] = []
        self._simular_fallo: bool = False

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self) -> None:
        """Carga estados operativos iniciales de ejemplo."""
        self._datos = [
            EstadoVuelo(
                id_vuelo="VUE-1001",
                aerolinea="AeroCaribe",
                numero_vuelo="AC-842",
                origen="BOG",
                destino="MIA",
                estado_actual="A TIEMPO",
                hora_salida_programada="2026-07-15T08:00:00Z",
                hora_salida_estimada="2026-07-15T08:00:00Z",
                puerta="B4",
                observaciones="Abordaje programado según itinerario original",
            ),
            EstadoVuelo(
                id_vuelo="VUE-1002",
                aerolinea="SkyGlobal",
                numero_vuelo="SG-815",
                origen="BOG",
                destino="MIA",
                estado_actual="RETRASADO",
                hora_salida_programada="2026-12-15T14:30:00Z",
                hora_salida_estimada="2026-12-15T16:15:00Z",
                puerta="C2",
                observaciones="Retraso operativo por tráfico aéreo en aeropuerto de salida",
            ),
            EstadoVuelo(
                id_vuelo="VUE-1003",
                aerolinea="AeroCaribe",
                numero_vuelo="AC-510",
                origen="BOG",
                destino="MIA",
                estado_actual="CANCELADO",
                hora_salida_programada="2026-12-20T11:00:00Z",
                hora_salida_estimada="2026-12-20T11:00:00Z",
                puerta="N/A",
                observaciones="Vuelo cancelado por condiciones meteorológicas adversas",
            ),
        ]

    # ── Control de disponibilidad / fallo (HTTP 503) ──────────

    def configurar_fallo(self, simular_fallo: bool) -> None:
        """Permite simular caída del proveedor externo o BD de aeropuertos."""
        self._simular_fallo = simular_fallo

    # ── Consultas y persistencia básica ───────────────────────

    def obtener_todos(self) -> list[EstadoVuelo]:
        if self._simular_fallo:
            raise ProveedorEstadoVueloError(
                "Error en el servicio de consulta de estados de vuelo"
            )
        return self._datos.copy()

    def obtener_por_id(self, id_vuelo: str) -> Optional[EstadoVuelo]:
        if self._simular_fallo:
            raise ProveedorEstadoVueloError(
                "Error en el servicio de consulta de estados de vuelo"
            )
        try:
            id_buscado = id_vuelo.strip().upper()
            return next(
                (vuelo for vuelo in self._datos if vuelo.id_vuelo.upper() == id_buscado),
                None,
            )
        except ProveedorEstadoVueloError:
            raise
        except Exception as exc:
            raise ProveedorEstadoVueloError(
                "Error en el servicio de consulta de estados de vuelo"
            ) from exc

    def actualizar_estado(
        self,
        id_vuelo: str,
        estado_actual: str,
        hora_salida_estimada: str,
        puerta: str,
        observaciones: str,
    ) -> Optional[EstadoVuelo]:
        if self._simular_fallo:
            raise ProveedorEstadoVueloError(
                "Error en el servicio de consulta de estados de vuelo"
            )
        vuelo = self.obtener_por_id(id_vuelo)
        if not vuelo:
            return None
        vuelo.estado_actual = estado_actual.strip().upper()
        vuelo.hora_salida_estimada = hora_salida_estimada
        vuelo.puerta = puerta.strip().upper()
        vuelo.observaciones = observaciones.strip()
        return vuelo


# Instancia única compartida (Singleton simple)
estado_vuelo_repository = EstadoVueloRepository()