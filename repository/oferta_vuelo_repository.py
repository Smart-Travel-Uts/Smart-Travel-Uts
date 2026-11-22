from typing import Optional
from domain.oferta_vuelo import OfertaVuelo, ProveedorOfertaError


class OfertaVueloRepository:

    def __init__(self) -> None:
        # Almacén en memoria: lista de objetos OfertaVuelo
        self._datos: list[OfertaVuelo] = []
        self._simular_fallo: bool = False

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self) -> None:
        """Carga datos iniciales de ejemplo de ofertas de vuelo."""
        self._datos = [
            OfertaVuelo(
                id_vuelo="VUE-1001",
                aerolinea="AeroCaribe",
                numero_vuelo="AC-402",
                origen="BOG",
                destino="MIA",
                hora_salida="2026-07-15T08:00:00Z",
                hora_llegada="2026-07-15T12:30:00Z",
                duracion_total="4h 30m",
                escalas=0,
                equipaje_permitido="1 pieza de mano (10kg) + 1 maleta en bodega (23kg)",
                precio_base=1_200_000.00,
                impuestos_tasas=150_000.00,
                politica_cancelacion="Permite cambios hasta 24 horas antes con penalización del 10%",
                moneda="COP",
                disponible=True,
            ),
            OfertaVuelo(
                id_vuelo="VUE-1002",
                aerolinea="SkyGlobal",
                numero_vuelo="SG-815",
                origen="BOG",
                destino="MIA",
                hora_salida="2026-12-15T14:30:00Z",
                hora_llegada="2026-12-15T20:15:00Z",
                duracion_total="5h 45m",
                escalas=1,
                equipaje_permitido="1 pieza de mano (10kg)",
                precio_base=1_350_000.00,
                impuestos_tasas=165_000.00,
                politica_cancelacion="No reembolsable; cambios sujetos a diferencia tarifaria",
                moneda="COP",
                disponible=True,
            ),
            OfertaVuelo(
                id_vuelo="VUE-1003",
                aerolinea="AeroCaribe",
                numero_vuelo="AC-510",
                origen="BOG",
                destino="MIA",
                hora_salida="2026-12-20T11:00:00Z",
                hora_llegada="2026-12-20T15:30:00Z",
                duracion_total="4h 30m",
                escalas=0,
                equipaje_permitido="1 pieza de mano (10kg) + 1 maleta en bodega (23kg)",
                precio_base=1_180_000.00,
                impuestos_tasas=145_000.00,
                politica_cancelacion="Permite cambios hasta 24 horas antes con penalización del 10%",
                moneda="COP",
                disponible=True,
            ),
            OfertaVuelo(
                id_vuelo="VUE-1004",
                aerolinea="SkyGlobal",
                numero_vuelo="SG-900",
                origen="BOG",
                destino="MDE",
                hora_salida="2026-11-10T07:00:00Z",
                hora_llegada="2026-11-10T08:00:00Z",
                duracion_total="1h 00m",
                escalas=0,
                equipaje_permitido="1 pieza de mano (10kg)",
                precio_base=320_000.00,
                impuestos_tasas=50_000.00,
                politica_cancelacion="No reembolsable",
                moneda="COP",
                disponible=False,
            ),
        ]

    # ── Control de disponibilidad / fallo (HTTP 503) ──────────

    def configurar_fallo(self, simular_fallo: bool) -> None:
        """Permite simular un fallo de conexión con la BD o proveedor."""
        self._simular_fallo = simular_fallo

    # ── Consultas ─────────────────────────────────────────────

    def obtener_todas(self) -> list[OfertaVuelo]:
        if self._simular_fallo:
            raise ProveedorOfertaError(
                "No fue posible consultar el detalle de la oferta en este momento"
            )
        return self._datos.copy()

    def obtener_por_id(self, id_vuelo: str) -> Optional[OfertaVuelo]:
        if self._simular_fallo:
            raise ProveedorOfertaError(
                "No fue posible consultar el detalle de la oferta en este momento"
            )
        try:
            id_buscado = id_vuelo.strip().upper()
            return next(
                (oferta for oferta in self._datos if oferta.id_vuelo.upper() == id_buscado),
                None,
            )
        except ProveedorOfertaError:
            raise
        except Exception as exc:
            raise ProveedorOfertaError(
                "No fue posible consultar el detalle de la oferta en este momento"
            ) from exc


# Instancia única compartida (Singleton simple)
oferta_vuelo_repository = OfertaVueloRepository()