from pydantic import ValidationError
from domain.oferta_vuelo import (
    COMISION_PLATAFORMA_PORCENTAJE,
    DetalleOfertaApiResponse,
    OfertaNoDisponibleError,
    OfertaVueloConsultaRequest,
    OfertaVueloDetalleResponse,
    ValidacionOfertaError,
)
from repository.oferta_vuelo_repository import (
    OfertaVueloRepository,
    oferta_vuelo_repository,
)


class OfertaVueloService:

    def __init__(self, repo: OfertaVueloRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def _validar_id_vuelo(self, id_vuelo: str) -> str:
        try:
            consulta = OfertaVueloConsultaRequest(id_vuelo=id_vuelo)
            return consulta.id_vuelo
        except ValidationError as exc:
            raise ValidacionOfertaError(
                "El formato del identificador de vuelo (id_vuelo) no es válido"
            ) from exc

    def listar(self) -> list[OfertaVueloDetalleResponse]:
        ofertas = self.repo.obtener_todas()
        return [
            OfertaVueloDetalleResponse(
                **oferta.to_response(comision_porcentaje=COMISION_PLATAFORMA_PORCENTAJE)
            )
            for oferta in ofertas
            if oferta.esta_disponible()
        ]

    def obtener(self, id_vuelo: str) -> OfertaVueloDetalleResponse:
        id_limpio = self._validar_id_vuelo(id_vuelo)
        oferta = self.repo.obtener_por_id(id_limpio)

        # Regla de negocio: la oferta debe existir y estar disponible
        if not oferta or not oferta.esta_disponible():
            raise OfertaNoDisponibleError(
                "La oferta de vuelo solicitada no existe o ya no se encuentra disponible"
            )

        return OfertaVueloDetalleResponse(
            **oferta.to_response(comision_porcentaje=COMISION_PLATAFORMA_PORCENTAJE)
        )

    def obtener_respuesta_detalle(self, id_vuelo: str) -> DetalleOfertaApiResponse:
        detalle = self.obtener(id_vuelo)
        return DetalleOfertaApiResponse(
            message="Detalle de oferta de vuelo obtenido exitosamente",
            data=detalle,
            success=True,
        )


# Instancia compartida lista para inyectar en el router
oferta_vuelo_service = OfertaVueloService(oferta_vuelo_repository)