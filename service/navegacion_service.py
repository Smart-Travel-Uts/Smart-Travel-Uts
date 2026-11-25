# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from pydantic import ValidationError
from domain.navegacion import (
    BusquedaPoisQuery,
    CentroBusquedaResponse,
    MapaPoisDataResponse,
    MapaPoisResponse,
    PuntoInteresResponse,
    ValidacionNavegacionError,
)
from repository.navegacion_repository import (
    NavegacionRepository,
    navegacion_repository,
)


class NavegacionService:

    def __init__(self, repo: NavegacionRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def _extraer_errores_validacion(self, exc: ValidationError) -> list[str]:
        errores: list[str] = []
        for err in exc.errors():
            msg = err.get("msg", "Parámetro inválido.")
            if msg.startswith("Value error, "):
                msg = msg.replace("Value error, ", "", 1)
            if msg not in errores:
                errores.append(msg)
        return errores or ["Parámetros de búsqueda inválidos."]

    def listar(self, latitud: float = 7.1193, longitud: float = -73.1227) -> list[PuntoInteresResponse]:
        pois = self.repo.obtener_todos()
        return [
            PuntoInteresResponse(
                **p.to_response(p.calcular_distancia_km(latitud, longitud))
            )
            for p in pois
            if p.activo
        ]

    def obtener_pois_mapa(
        self,
        latitud: float,
        longitud: float,
        radio_km: float = 3.0,
        categoria: Optional[str] = None,
        limite: int = 50,
    ) -> MapaPoisResponse:
        # BusquedaPoisQuery ya valida coordenadas, radio_km, categoría y límite en el dominio
        try:
            query = BusquedaPoisQuery(
                latitud   = latitud,
                longitud  = longitud,
                radio_km  = radio_km,
                categoria = categoria,
                limite    = limite,
            )
        except ValidationError as exc:
            raise ValidacionNavegacionError(
                "; ".join(self._extraer_errores_validacion(exc))
            ) from exc

        todos_pois = self.repo.obtener_todos()

        # Regla de negocio: filtrar POIs activos dentro del radio y categoría, calculando distancia
        coincidencias: list[tuple[float, PuntoInteresResponse]] = []
        for poi in todos_pois:
            coincide, distancia = poi.coincide_busqueda(
                lat_origen = query.latitud,
                lon_origen = query.longitud,
                radio_km   = query.radio_km,
                categoria  = query.categoria,
            )
            if coincide:
                coincidencias.append(
                    (distancia, PuntoInteresResponse(**poi.to_response(distancia)))
                )

        # Regla de negocio: ordenar de menor a mayor distancia y respetar límite
        coincidencias.sort(key=lambda par: par[0])
        pois_ordenados = [item for _, item in coincidencias[: query.limite]]

        mensaje = (
            "Puntos de interés recuperados exitosamente"
            if pois_ordenados
            else "No se encontraron puntos de interés dentro del radio especificado"
        )

        return MapaPoisResponse(
            message = mensaje,
            data    = MapaPoisDataResponse(
                centro_busqueda = CentroBusquedaResponse(
                    latitud  = query.latitud,
                    longitud = query.longitud,
                ),
                radio_aplicado_km = query.radio_km,
                total_pois        = len(pois_ordenados),
                puntos_interes    = pois_ordenados,
            ),
            success = True,
        )

    def por_categoria(
        self,
        categoria: str,
        latitud: float = 7.1193,
        longitud: float = -73.1227,
        radio_km: float = 10.0,
    ) -> MapaPoisResponse:
        return self.obtener_pois_mapa(
            latitud   = latitud,
            longitud  = longitud,
            radio_km  = radio_km,
            categoria = categoria,
        )


# Instancia compartida lista para inyectar en el router
navegacion_service = NavegacionService(navegacion_repository)