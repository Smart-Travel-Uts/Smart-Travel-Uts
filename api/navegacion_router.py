# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from domain.navegacion import (
    CATEGORIAS_POI,
    ErrorNavegacionDataResponse,
    ErrorNavegacionResponse,
    MapaPoisResponse,
    ServicioCartografiaError,
    ValidacionNavegacionError,
)
from repository.navegacion_repository import navegacion_repository
from service.navegacion_service import NavegacionService

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/navegacion",
    tags=["Navegación"],
)

# Instanciar el servicio con inyección del repositorio
service = NavegacionService(repo=navegacion_repository)


def _respuesta_error_400(mensaje_error: str) -> JSONResponse:
    errores = [e.strip() for e in mensaje_error.split(";") if e.strip()]
    cuerpo = ErrorNavegacionResponse(
        message="Error en la validación de parámetros de búsqueda",
        data=ErrorNavegacionDataResponse(errores=errores or [mensaje_error]),
        success=False,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=cuerpo.model_dump(),
    )


# ── GET /api/v1/navegacion/mapa/pois ──────────────────────────
@router.get(
    "/mapa/pois",
    response_model=MapaPoisResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "model": ErrorNavegacionResponse,
            "description": "Parámetros de búsqueda inválidos",
        },
        503: {
            "description": "Servicio de cartografía no disponible temporalmente",
        },
    },
)
def obtener_pois_mapa(
    latitud: float = Query(..., description="Coordenada WGS84 de origen (-90.0 a 90.0)"),
    longitud: float = Query(..., description="Coordenada WGS84 de origen (-180.0 a 180.0)"),
    radio_km: float = Query(3.0, description="Radio en km (> 0 y <= 50)"),
    categoria: Optional[CATEGORIAS_POI] = Query(
        None,
        description="Categoría: GASTRONOMIA, CULTURA, PARQUE_CULTURAL, TRANSPORTE, HISTORIA",
    ),
    limite: int = Query(50, description="Límite de POIs a retornar"),
):
    """Retorna POIs cercanos en formato GeoJSON ordenados por distancia."""
    try:
        return service.obtener_pois_mapa(
            latitud=latitud,
            longitud=longitud,
            radio_km=radio_km,
            categoria=categoria,
            limite=limite,
        )
    except ValidacionNavegacionError as e:
        return _respuesta_error_400(str(e))
    except ServicioCartografiaError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )