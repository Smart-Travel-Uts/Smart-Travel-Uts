# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from domain.hospedaje import Alojamiento, ProveedorHospedajeError


class HospedajeRepository:

    def __init__(self) -> None:
        # Almacén en memoria: lista de objetos Alojamiento
        self._datos: list[Alojamiento] = []
        self._siguiente_numero: int = 2044
        self._simular_fallo: bool = False

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self) -> None:
        """Carga alojamientos iniciales de ejemplo."""
        iniciales = [
            Alojamiento(
                id_alojamiento="ALO-2041",
                nombre="Hotel Cabecera Real",
                tipo_alojamiento="HOTEL",
                ciudad="Bucaramanga",
                calificacion_promedio=4.6,
                precio_noche_base=180000.00,
                moneda="COP",
                servicios_destacados=["WIFI", "DESAYUNO_INCLUIDO", "PARQUEADERO"],
                capacidad_maxima=4,
                cupo_disponible=True,
                check_in="15:00",
                check_out="12:00",
                cancelacion="Reembolso del 100% hasta 72 horas antes; 50% entre 24 y 72 horas; sin reembolso con menos de 24 horas.",
                restricciones=["No se permiten mascotas sin notificación previa"],
            ),
            Alojamiento(
                id_alojamiento="ALO-2042",
                nombre="Apartamentos Cañaveral Suite",
                tipo_alojamiento="DEPARTAMENTO",
                ciudad="Bucaramanga",
                calificacion_promedio=4.8,
                precio_noche_base=240000.00,
                moneda="COP",
                servicios_destacados=["WIFI", "COCINA_EQUIPADA", "PISCINA"],
                capacidad_maxima=6,
                cupo_disponible=True,
                check_in="15:00",
                check_out="11:00",
                cancelacion="Reembolso del 100% hasta 48 horas antes; sin reembolso con menos de 48 horas.",
                restricciones=["Prohibido fumar en interiores"],
            ),
            Alojamiento(
                id_alojamiento="ALO-2043",
                nombre="Hostal Chicamocha Backpackers",
                tipo_alojamiento="HOSTAL",
                ciudad="San Gil",
                calificacion_promedio=4.2,
                precio_noche_base=75000.00,
                moneda="COP",
                servicios_destacados=["WIFI", "TERRAZA", "CAFE_GRATIS"],
                capacidad_maxima=3,
                cupo_disponible=False,
                check_in="14:00",
                check_out="11:00",
                cancelacion="Reembolso del 100% hasta 24 horas antes.",
                restricciones=["Silencio obligatorio después de las 22:00"],
            ),
        ]
        self._datos = iniciales
        self._siguiente_numero = 2044

    # ── Control de disponibilidad / fallo (HTTP 503) ──────────

    def configurar_fallo(self, simular_fallo: bool) -> None:
        """Permite simular caída o timeout del proveedor externo o BD de alojamientos."""
        self._simular_fallo = simular_fallo

    # ── Consultas y persistencia básica ───────────────────────

    def obtener_todos(self) -> list[Alojamiento]:
        if self._simular_fallo:
            raise ProveedorHospedajeError(
                "Servicio de consulta de hospedaje temporalmente no disponible."
            )
        return self._datos.copy()

    def obtener_por_id(self, id_alojamiento: str) -> Optional[Alojamiento]:
        if self._simular_fallo:
            raise ProveedorHospedajeError(
                "Servicio de consulta de hospedaje temporalmente no disponible."
            )
        try:
            id_buscado = id_alojamiento.strip().upper()
            return next(
                (item for item in self._datos if item.id_alojamiento.upper() == id_buscado),
                None,
            )
        except ProveedorHospedajeError:
            raise
        except Exception as exc:
            raise ProveedorHospedajeError(
                "Servicio de consulta de hospedaje temporalmente no disponible."
            ) from exc

    def obtener_por_ciudad(self, ciudad: str) -> list[Alojamiento]:
        if self._simular_fallo:
            raise ProveedorHospedajeError(
                "Servicio de consulta de hospedaje temporalmente no disponible."
            )
        destino_limpio = ciudad.strip().lower()
        return [
            item for item in self._datos
            if destino_limpio in item.ciudad.lower()
        ]

    def crear(
        self,
        nombre: str,
        tipo_alojamiento: str,
        ciudad: str,
        calificacion_promedio: float,
        precio_noche_base: float,
        moneda: str,
        servicios_destacados: list[str],
        capacidad_maxima: int,
        cupo_disponible: bool = True,
        check_in: str = "15:00",
        check_out: str = "12:00",
        cancelacion: str = "Reembolso del 100% hasta 48 horas antes.",
        restricciones: Optional[list[str]] = None,
    ) -> Alojamiento:
        nuevo = Alojamiento(
            id_alojamiento=f"ALO-{self._siguiente_numero}",
            nombre=nombre,
            tipo_alojamiento=tipo_alojamiento,
            ciudad=ciudad,
            calificacion_promedio=calificacion_promedio,
            precio_noche_base=precio_noche_base,
            moneda=moneda,
            servicios_destacados=servicios_destacados,
            capacidad_maxima=capacidad_maxima,
            cupo_disponible=cupo_disponible,
            check_in=check_in,
            check_out=check_out,
            cancelacion=cancelacion,
            restricciones=restricciones or [],
        )
        self._datos.append(nuevo)
        self._siguiente_numero += 1
        return nuevo

    def eliminar(self, id_alojamiento: str) -> bool:
        alojamiento = self.obtener_por_id(id_alojamiento)
        if not alojamiento:
            return False
        self._datos.remove(alojamiento)
        return True


# Instancia única compartida (Singleton simple)
hospedaje_repository = HospedajeRepository()