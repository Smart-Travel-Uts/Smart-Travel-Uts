# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from datetime import datetime, timedelta, timezone
from typing import Optional
from domain.clima import (
    ErrorClimaDataResponse,
    ErrorClimaResponse,
    PronosticoDataResponse,
    PronosticoDestino,
    PronosticoResponse,
)
from repository.clima_repository import ClimaRepository, clima_repository


class ValidacionClimaError(Exception):
    """Error en parámetros de ubicación o rango de días (HTTP 400)."""

    def __init__(self, errores: list[str], message: str = "Parámetros de geolocalización o rango de días inválidos"):
        super().__init__(message)
        self.message = message
        self.errores = errores

    def to_response_dict(self) -> dict:
        return ErrorClimaResponse(
            message=self.message,
            data=ErrorClimaDataResponse(errores=self.errores),
            success=False,
        ).model_dump()


class ProveedorClimaNoDisponibleError(Exception):
    """Fallo del proveedor externo sin caché disponible (HTTP 503)."""


class ClimaService:
    TTL_CACHE = timedelta(minutes=15)

    def __init__(self, repo: ClimaRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def _resolver_ubicacion(
        self,
        latitud: Optional[float],
        longitud: Optional[float],
        id_destino: Optional[str],
    ) -> tuple[str, float, float]:
        errores: list[str] = []

        tiene_coords = latitud is not None or longitud is not None
        destino_limpio = id_destino.strip().upper() if id_destino and id_destino.strip() else None

        if not tiene_coords and not destino_limpio:
            errores.append(
                "Debe proveer coordenadas válidas (latitud y longitud) o un id_destino válido"
            )
            raise ValidacionClimaError(errores)

        if tiene_coords:
            if latitud is None or longitud is None:
                errores.append(
                    "Debe enviar tanto latitud como longitud cuando consulta por coordenadas"
                )
            else:
                if not (-90.0 <= float(latitud) <= 90.0):
                    errores.append("La latitud debe estar dentro del rango [-90.0, 90.0]")
                if not (-180.0 <= float(longitud) <= 180.0):
                    errores.append("La longitud debe estar dentro del rango [-180.0, 180.0]")

            if errores:
                raise ValidacionClimaError(errores)

            assert latitud is not None and longitud is not None
            lat_red = round(float(latitud), 4)
            lon_red = round(float(longitud), 4)
            nombre = (
                "Bucaramanga, Santander"
                if (lat_red == 7.1193 and lon_red == -73.1227)
                else f"Ubicación ({lat_red}, {lon_red})"
            )
            return nombre, lat_red, lon_red

        assert destino_limpio is not None
        destino = self.repo.obtener_destino_por_id(destino_limpio)
        if not destino:
            raise ValidacionClimaError(
                [f"El id_destino '{destino_limpio}' no es válido o no existe"]
            )
        return (
            destino["nombre"],
            float(destino["latitud"]),
            float(destino["longitud"]),
        )

    def _validar_parametros_consulta(
        self,
        latitud: Optional[float],
        longitud: Optional[float],
        id_destino: Optional[str],
        dias: int,
        unidades: str,
    ) -> tuple[str, float, float, int, str]:
        errores: list[str] = []
        nombre, lat, lon = "", 0.0, 0.0

        try:
            nombre, lat, lon = self._resolver_ubicacion(latitud, longitud, id_destino)
        except ValidacionClimaError as exc:
            errores.extend(exc.errores)

        if not (1 <= int(dias) <= 7):
            errores.append(
                "El parámetro 'dias' no puede superar el límite máximo de 7 (rango permitido: 1 a 7)"
            )

        unidades_limpias = (unidades or "CELSIUS").strip().upper()
        if unidades_limpias not in {"CELSIUS", "FAHRENHEIT"}:
            errores.append("El parámetro 'unidades' debe ser CELSIUS o FAHRENHEIT")

        if errores:
            raise ValidacionClimaError(errores)

        return nombre, lat, lon, int(dias), unidades_limpias

    def _obtener_pronostico_con_cache(
        self, nombre: str, lat: float, lon: float
    ) -> tuple[PronosticoDestino, Optional[bool]]:
        clave = f"{lat}:{lon}"
        ahora = datetime.now(timezone.utc)
        entrada_cache = self.repo.obtener_cache(clave)

        # 1. Si hay caché vigente (dentro de 15 min), devolver desde caché
        if entrada_cache:
            guardado_en: datetime = entrada_cache["guardado_en"]
            if (ahora - guardado_en) <= self.TTL_CACHE:
                return entrada_cache["pronostico"], None

        # 2. Intentar consultar el proveedor externo
        if self.repo.simular_fallo_proveedor:
            if entrada_cache:
                return entrada_cache["pronostico"], True
            raise ProveedorClimaNoDisponibleError(
                "Proveedor meteorológico externo no disponible y sin datos en caché"
            )

        pronostico = self.repo.obtener_pronostico_proveedor(nombre, lat, lon)
        self.repo.guardar_cache(clave, pronostico, ahora)
        return pronostico, None

    def consultar_pronostico(
        self,
        latitud: Optional[float] = None,
        longitud: Optional[float] = None,
        id_destino: Optional[str] = None,
        dias: int = 3,
        unidades: str = "CELSIUS",
    ) -> PronosticoResponse:
        nombre, lat, lon, dias_validos, unidades_validas = self._validar_parametros_consulta(
            latitud=latitud,
            longitud=longitud,
            id_destino=id_destino,
            dias=dias,
            unidades=unidades,
        )

        pronostico, dato_obsoleto = self._obtener_pronostico_con_cache(
            nombre=nombre,
            lat=lat,
            lon=lon,
        )

        payload = pronostico.to_response(
            dias=dias_validos,
            unidades=unidades_validas,
            dato_obsoleto=dato_obsoleto,
        )
        return PronosticoResponse(
            message="Pronóstico meteorológico y alertas obtenidas exitosamente",
            data=PronosticoDataResponse(**payload),
            success=True,
        )


# Instancia única compartida
clima_service = ClimaService(clima_repository)