# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from domain.clima import ErrorClimaResponse, PronosticoResponse
from repository.clima_repository import clima_repository
from service.clima_service import (
    ClimaService,
    ProveedorClimaNoDisponibleError,
    ValidacionClimaError,
)

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/clima",
    tags=["Clima y Alertas"],
)

# Instanciar el servicio con inyección del repositorio
service = ClimaService(repo=clima_repository)


# ── GET /api/v1/clima/pronostico ──────────────────────────────
@router.get(
    "/pronostico",
    response_model=PronosticoResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorClimaResponse},
        503: {"model": ErrorClimaResponse},
    },
)
def obtener_pronostico(
    latitud: Optional[float] = Query(None, description="Latitud WGS84 [-90.0, 90.0]"),
    longitud: Optional[float] = Query(None, description="Longitud WGS84 [-180.0, 180.0]"),
    id_destino: Optional[str] = Query(None, description="ID del destino, ej. DEST-BGA"),
    dias: int = Query(3, description="Cantidad de días a pronosticar (1 a 7)"),
    unidades: str = Query("CELSIUS", description="Sistema de unidades: CELSIUS o FAHRENHEIT"),
):
    """Retorna el pronóstico meteorológico y alertas locales para un destino."""
    try:
        return service.consultar_pronostico(
            latitud=latitud,
            longitud=longitud,
            id_destino=id_destino,
            dias=dias,
            unidades=unidades,
        )
    except ValidacionClimaError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=e.to_response_dict(),
        )
    except ProveedorClimaNoDisponibleError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )