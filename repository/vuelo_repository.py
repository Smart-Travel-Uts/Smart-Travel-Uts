from typing import List, Optional
from domain.vuelo import ProveedorVuelosError, Vuelo


class VueloRepository:

    def __init__(self) -> None:
        self._datos: list[Vuelo] = []
        self._simular_fallo: bool = False
        self._seed()

    def _seed(self) -> None:
        """Carga datos iniciales de ejemplo con fecha de retorno definida."""
        self._datos = [
            Vuelo(
                id_vuelo="VUE-1001",
                aerolinea="AeroCaribe",
                origen="BOG",
                destino="MIA",
                fecha_salida="2026-12-15T08:00:00Z",
                fecha_retorno="2026-12-25",
                precio_base=1_200_000.00,
                moneda="COP",
                asientos_disponibles=14,
            ),
            Vuelo(
                id_vuelo="VUE-1002",
                aerolinea="SkyGlobal",
                origen="BOG",
                destino="MIA",
                fecha_salida="2026-12-15T14:30:00Z",
                fecha_retorno="2027-01-10",
                precio_base=1_350_000.00,
                moneda="COP",
                asientos_disponibles=8,
            ),
            Vuelo(
                id_vuelo="VUE-1003",
                aerolinea="AeroCaribe",
                origen="BOG",
                destino="MIA",
                fecha_salida="2026-12-20T11:00:00Z",
                fecha_retorno="2026-12-30",
                precio_base=1_180_000.00,
                moneda="COP",
                asientos_disponibles=10,
            ),
        ]

    def configurar_fallo(self, simular_fallo: bool) -> None:
        """Permite simular un fallo del proveedor externo de vuelos (HTTP 503)."""
        self._simular_fallo = simular_fallo

    def obtener_todos(self) -> list[Vuelo]:
        if self._simular_fallo:
            raise ProveedorVuelosError(
                "No fue posible consultar los servicios de vuelos en este momento"
            )
        return self._datos.copy()

    def obtener_por_id(self, id_vuelo: str) -> Optional[Vuelo]:
        if self._simular_fallo:
            raise ProveedorVuelosError(
                "No fue posible consultar los servicios de vuelos en este momento"
            )
        return next((v for v in self._datos if v.id_vuelo == id_vuelo), None)

    def buscar_vuelos(
        self,
        origen: str,
        destino: str,
        fecha_ida: str,
        pasajeros: int,
        fecha_retorno: Optional[str] = None,
    ) -> List[Vuelo]:
        if self._simular_fallo:
            raise ProveedorVuelosError(
                "No fue posible consultar los servicios de vuelos en este momento"
            )
        try:
            resultados: List[Vuelo] = []
            for vuelo in self._datos:
                coincide_base = (
                    vuelo.origen == origen
                    and vuelo.destino == destino
                    and vuelo.fecha_salida.startswith(fecha_ida)
                    and vuelo.tiene_asientos(pasajeros)
                )
                if not coincide_base:
                    continue

                if fecha_retorno is not None and vuelo.fecha_retorno != fecha_retorno:
                    continue

                resultados.append(vuelo)
            return resultados
        except ProveedorVuelosError:
            raise
        except Exception as exc:
            raise ProveedorVuelosError(
                "No fue posible consultar los servicios de vuelos en este momento"
            ) from exc


vuelo_repository = VueloRepository()