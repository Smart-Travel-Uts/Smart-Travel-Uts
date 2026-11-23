# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import ValidationError
from domain.estado_vuelo import (
    ConsultaEstadoVueloResponse,
    EstadoVueloConsultaRequest,
    EstadoVueloDataResponse,
    ValidacionEstadoVueloError,
    VueloNoEncontradoError,
)
from repository.estado_vuelo_repository import (
    EstadoVueloRepository,
    estado_vuelo_repository,
)


class EstadoVueloService:

    def __init__(self, repo: EstadoVueloRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def _validar_id_vuelo(self, id_vuelo: str) -> str:
        try:
            consulta = EstadoVueloConsultaRequest(id_vuelo=id_vuelo)
            return consulta.id_vuelo
        except ValidationError as exc:
            raise ValidacionEstadoVueloError(
                "El formato del identificador de vuelo (id_vuelo) no es válido"
            ) from exc

    def listar(self) -> list[EstadoVueloDataResponse]:
        return [
            EstadoVueloDataResponse(**vuelo.to_response())
            for vuelo in self.repo.obtener_todos()
        ]

    def obtener(self, id_vuelo: str) -> EstadoVueloDataResponse:
        id_limpio = self._validar_id_vuelo(id_vuelo)
        vuelo = self.repo.obtener_por_id(id_limpio)

        # Regla de negocio: el vuelo debe existir en el sistema
        if not vuelo:
            raise VueloNoEncontradoError(
                "El vuelo indicado no existe o no se encuentra registrado en el sistema"
            )

        return EstadoVueloDataResponse(**vuelo.to_response())

    def obtener_respuesta_estado(self, id_vuelo: str) -> ConsultaEstadoVueloResponse:
        detalle = self.obtener(id_vuelo)
        return ConsultaEstadoVueloResponse(
            message="Consulta de estado de vuelo exitosa",
            data=detalle,
            success=True,
        )

    def actualizar_estado(
        self,
        id_vuelo: str,
        estado_actual: str,
        hora_salida_estimada: str,
        puerta: str,
        observaciones: str,
    ) -> EstadoVueloDataResponse:
        id_limpio = self._validar_id_vuelo(id_vuelo)
        vuelo = self.repo.actualizar_estado(
            id_vuelo=id_limpio,
            estado_actual=estado_actual,
            hora_salida_estimada=hora_salida_estimada,
            puerta=puerta,
            observaciones=observaciones,
        )
        if not vuelo:
            raise VueloNoEncontradoError(
                "El vuelo indicado no existe o no se encuentra registrado en el sistema"
            )
        return EstadoVueloDataResponse(**vuelo.to_response())


# Instancia compartida lista para inyectar en el router
estado_vuelo_service = EstadoVueloService(estado_vuelo_repository)