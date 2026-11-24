# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from datetime import date
from typing import Optional
from pydantic import ValidationError
from domain.hospedaje import (
    AlojamientoNoEncontradoError,
    AlojamientoResumenResponse,
    BusquedaHospedajeDataResponse,
    BusquedaHospedajeQuery,
    BusquedaHospedajeResponse,
    DisponibilidadDataResponse,
    DisponibilidadHospedajeQuery,
    DisponibilidadHospedajeResponse,
    ValidacionHospedajeError,
)
from repository.hospedaje_repository import (
    HospedajeRepository,
    hospedaje_repository,
)


class HospedajeService:

    def __init__(self, repo: HospedajeRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def _extraer_errores_validacion(self, exc: ValidationError) -> list[str]:
        errores: list[str] = []
        for err in exc.errors():
            msg = err.get("msg", "Parámetro inválido.")
            if msg.startswith("Value error, "):
                msg = msg.replace("Value error, ", "", 1)
            errores.append(msg)
        return errores or ["Parámetros de consulta inválidos."]

    def listar(self) -> list[AlojamientoResumenResponse]:
        return [
            AlojamientoResumenResponse(**a.to_response())
            for a in self.repo.obtener_todos()
        ]

    def buscar(
        self,
        destino: str,
        fecha_entrada: date,
        fecha_salida: date,
        huespedes: int = 1,
        precio_min: Optional[float] = None,
        precio_max: Optional[float] = None,
        calificacion_min: Optional[float] = None,
    ) -> BusquedaHospedajeResponse:
        # BusquedaHospedajeQuery ya valida destino, fechas y rangos en el dominio
        try:
            query = BusquedaHospedajeQuery(
                destino          = destino,
                fecha_entrada    = fecha_entrada,
                fecha_salida     = fecha_salida,
                huespedes        = huespedes,
                precio_min       = precio_min,
                precio_max       = precio_max,
                calificacion_min = calificacion_min,
            )
        except ValidationError as exc:
            raise ValidacionHospedajeError(
                "; ".join(self._extraer_errores_validacion(exc))
            ) from exc

        alojamientos = self.repo.obtener_todos()
        filtrados = [
            AlojamientoResumenResponse(**a.to_response())
            for a in alojamientos
            if a.coincide_busqueda(
                destino          = query.destino,
                huespedes        = query.huespedes,
                precio_min       = query.precio_min,
                precio_max       = query.precio_max,
                calificacion_min = query.calificacion_min,
            )
        ]

        return BusquedaHospedajeResponse(
            message = "Búsqueda de alojamientos exitosa",
            data    = BusquedaHospedajeDataResponse(
                total_resultados = len(filtrados),
                alojamientos     = filtrados,
            ),
            success = True,
        )

    def consultar_disponibilidad(
        self,
        id_alojamiento: str,
        fecha_entrada: date,
        fecha_salida: date,
        huespedes: int,
    ) -> DisponibilidadHospedajeResponse:
        if not id_alojamiento or not id_alojamiento.strip():
            raise ValidacionHospedajeError(
                "El identificador del alojamiento es obligatorio."
            )

        try:
            query = DisponibilidadHospedajeQuery(
                fecha_entrada = fecha_entrada,
                fecha_salida  = fecha_salida,
                huespedes     = huespedes,
            )
        except ValidationError as exc:
            raise ValidacionHospedajeError(
                "; ".join(self._extraer_errores_validacion(exc))
            ) from exc

        alojamiento = self.repo.obtener_por_id(id_alojamiento)
        if not alojamiento:
            raise AlojamientoNoEncontradoError(
                f"El alojamiento '{id_alojamiento.strip().upper()}' no existe o no se encuentra disponible."
            )

        # Regla de negocio: confirmar cupo real para huéspedes en las fechas solicitadas
        if not alojamiento.tiene_cupo(query.huespedes):
            raise AlojamientoNoEncontradoError(
                f"El alojamiento '{alojamiento.id_alojamiento}' no tiene cupo disponible para {query.huespedes} huéspedes."
            )

        payload = alojamiento.to_disponibilidad_response(
            fecha_entrada = query.fecha_entrada,
            fecha_salida  = query.fecha_salida,
            huespedes     = query.huespedes,
        )
        return DisponibilidadHospedajeResponse(
            message = "Disponibilidad y tarifa de alojamiento confirmadas",
            data    = DisponibilidadDataResponse(**payload),
            success = True,
        )

    def por_ciudad(self, ciudad: str) -> list[AlojamientoResumenResponse]:
        alojamientos = self.repo.obtener_por_ciudad(ciudad)
        if not alojamientos:
            raise AlojamientoNoEncontradoError(
                f"No hay alojamientos registrados en '{ciudad}'"
            )
        return [AlojamientoResumenResponse(**a.to_response()) for a in alojamientos]


# Instancia compartida lista para inyectar en el router
hospedaje_service = HospedajeService(hospedaje_repository)