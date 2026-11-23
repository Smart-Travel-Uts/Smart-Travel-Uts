# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from domain.estado_vuelo import (
    ConsultaEstadoVueloResponse,
    ProveedorEstadoVueloError,
    ValidacionEstadoVueloError,
    VueloNoEncontradoDataResponse,
    VueloNoEncontradoError,
    VueloNoEncontradoResponse,
)
from repository.estado_vuelo_repository import estado_vuelo_repository
from service.estado_vuelo_service import EstadoVueloService

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/logistica/vuelos",
    tags=["Logística - Vuelos"],
)

# Instanciar el servicio con inyección del repositorio
service = EstadoVueloService(repo=estado_vuelo_repository)


# ── GET /api/v1/logistica/vuelos/{id_vuelo}/estado ───────────
@router.get(
    "/{id_vuelo}/estado",
    response_model=ConsultaEstadoVueloResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Formato de identificador de vuelo inválido"},
        404: {
            "model": VueloNoEncontradoResponse,
            "description": "El vuelo no existe o no está registrado en el sistema",
        },
        503: {"description": "Error en el servicio de consulta de estados de vuelo"},
    },
)
def consultar_estado_vuelo(id_vuelo: str):
    """Retorna el estado operativo actual de un vuelo por su ID."""
    try:
        return service.obtener_respuesta_estado(id_vuelo)
    except ValidacionEstadoVueloError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VueloNoEncontradoError as e:
        cuerpo_404 = VueloNoEncontradoResponse(
            mensaje=str(e),
            data=VueloNoEncontradoDataResponse(
                id_vuelo=id_vuelo.strip().upper(),
                estado_actual="DESCONOCIDO",
            ),
            success=False,
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=cuerpo_404.model_dump(),
        )
    except ProveedorEstadoVueloError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )