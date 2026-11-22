# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from domain.oferta_vuelo import (
    DetalleOfertaApiResponse,
    OfertaNoDisponibleError,
    OfertaNoDisponibleResponse,
    ProveedorOfertaError,
    ValidacionOfertaError,
)
from repository.oferta_vuelo_repository import oferta_vuelo_repository
from service.oferta_vuelo_service import OfertaVueloService

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/logistica/vuelos",
    tags=["Logística - Vuelos"],
)

# Instanciar el servicio con inyección del repositorio
service = OfertaVueloService(repo=oferta_vuelo_repository)


# ── GET /api/v1/logistica/vuelos/oferta/{id_vuelo} ───────────
@router.get(
    "/oferta/{id_vuelo}",
    response_model=DetalleOfertaApiResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Formato de ID de vuelo inválido"},
        404: {
            "model": OfertaNoDisponibleResponse,
            "description": "La oferta de vuelo no existe o ya no se encuentra disponible",
        },
        503: {"description": "Error de conexión con la base de datos o proveedor"},
    },
)
def obtener_detalle_oferta(id_vuelo: str):
    """Retorna el detalle completo de una oferta de vuelo por su ID."""
    try:
        return service.obtener_respuesta_detalle(id_vuelo)
    except ValidacionOfertaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except OfertaNoDisponibleError as e:
        cuerpo_404 = OfertaNoDisponibleResponse(
            mensaje=str(e),
            data=None,
            success=False,
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=cuerpo_404.model_dump(),
        )
    except ProveedorOfertaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )