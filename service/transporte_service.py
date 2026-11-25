# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from pydantic import ValidationError
from domain.transporte import (
    BusquedaRutasQuery,
    OpcionRutaResponse,
    PuntoGeolocalizadoResponse,
    RutasTransporteDataResponse,
    RutasTransporteResponse,
    ValidacionTransporteError,
)
from repository.transporte_repository import (
    TransporteRepository,
    transporte_repository,
)


class TransporteService:

    def __init__(self, repo: TransporteRepository):
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
        return errores or ["Parámetros de geolocalización o itinerario inválidos."]

    def _resolver_direccion_cercana(self, lat: float, lon: float, es_origen: bool) -> str:
        if round(lat, 3) == 7.119 and round(lon, 3) == -73.123:
            return "Calle 36 # 21-14, Centro"
        if round(lat, 3) == 7.138 and round(lon, 3) == -73.118:
            return "Unidades Tecnológicas de Santander"
        return (
            f"Punto de origen ({round(lat, 4)}, {round(lon, 4)})"
            if es_origen
            else f"Punto de destino ({round(lat, 4)}, {round(lon, 4)})"
        )

    def listar(
        self,
        latitud_origen: float = 7.1193,
        longitud_origen: float = -73.1227,
        latitud_destino: float = 7.1381,
        longitud_destino: float = -73.1182,
    ) -> list[OpcionRutaResponse]:
        respuesta = self.consultar_rutas(
            latitud_origen=latitud_origen,
            longitud_origen=longitud_origen,
            latitud_destino=latitud_destino,
            longitud_destino=longitud_destino,
        )
        return respuesta.data.opciones_ruta

    def obtener(self, id_ruta: str) -> OpcionRutaResponse:
        ruta = self.repo.obtener_por_id(id_ruta)
        if not ruta:
            raise ValidacionTransporteError(f"Ruta con id {id_ruta} no encontrada")
        query_base = BusquedaRutasQuery(
            latitud_origen=ruta.lat_inicio,
            longitud_origen=ruta.lon_inicio,
            latitud_destino=ruta.lat_fin,
            longitud_destino=ruta.lon_fin,
        )
        return OpcionRutaResponse(**ruta.to_response(query_base.obtener_hora_salida_dt()))

    def consultar_rutas(
        self,
        latitud_origen: float,
        longitud_origen: float,
        latitud_destino: float,
        longitud_destino: float,
        hora_salida: Optional[str] = None,
        tipo_transporte: Optional[str] = None,
    ) -> RutasTransporteResponse:
        # BusquedaRutasQuery valida rangos WGS84, origen != destino, hora_salida y tipo_transporte
        try:
            query = BusquedaRutasQuery(
                latitud_origen=latitud_origen,
                longitud_origen=longitud_origen,
                latitud_destino=latitud_destino,
                longitud_destino=longitud_destino,
                hora_salida=hora_salida,
                tipo_transporte=tipo_transporte,
            )
        except ValidationError as exc:
            raise ValidacionTransporteError(
                "; ".join(self._extraer_errores_validacion(exc))
            ) from exc

        hora_salida_dt = query.obtener_hora_salida_dt()
        rutas = self.repo.obtener_todos()

        # Regla de negocio: filtrar rutas activas que cubran origen, destino y modo solicitado
        opciones: list[OpcionRutaResponse] = []
        for ruta in rutas:
            if ruta.cubre_trayecto(
                lat_origen=query.latitud_origen,
                lon_origen=query.longitud_origen,
                lat_destino=query.latitud_destino,
                lon_destino=query.longitud_destino,
                tipo_transporte=query.tipo_transporte,
            ):
                opciones.append(OpcionRutaResponse(**ruta.to_response(hora_salida_dt)))

        # Regla de negocio: priorizar menor tiempo estimado de viaje
        opciones.sort(key=lambda op: op.duracion_estimada_minutos)

        mensaje = (
            "Rutas de transporte urbano calculadas exitosamente"
            if opciones
            else "No se encontraron opciones de transporte urbano entre los puntos especificados"
        )

        return RutasTransporteResponse(
            message=mensaje,
            data=RutasTransporteDataResponse(
                origen=PuntoGeolocalizadoResponse(
                    latitud=query.latitud_origen,
                    longitud=query.longitud_origen,
                    direccion_cercana=self._resolver_direccion_cercana(
                        query.latitud_origen, query.longitud_origen, es_origen=True
                    ),
                ),
                destino=PuntoGeolocalizadoResponse(
                    latitud=query.latitud_destino,
                    longitud=query.longitud_destino,
                    direccion_cercana=self._resolver_direccion_cercana(
                        query.latitud_destino, query.longitud_destino, es_origen=False
                    ),
                ),
                total_opciones=len(opciones),
                opciones_ruta=opciones,
            ),
            success=True,
        )

    def por_tipo(
        self,
        tipo_transporte: str,
        latitud_origen: float = 7.1193,
        longitud_origen: float = -73.1227,
        latitud_destino: float = 7.1381,
        longitud_destino: float = -73.1182,
    ) -> RutasTransporteResponse:
        return self.consultar_rutas(
            latitud_origen=latitud_origen,
            longitud_origen=longitud_origen,
            latitud_destino=latitud_destino,
            longitud_destino=longitud_destino,
            tipo_transporte=tipo_transporte,
        )


# Instancia compartida lista para inyectar en el router
transporte_service = TransporteService(transporte_repository)