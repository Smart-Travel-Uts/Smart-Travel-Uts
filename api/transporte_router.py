# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from domain.transporte import (
    ErrorTransporteDataResponse,
    ErrorTransporteResponse,
    RutasTransporteResponse,
    ServicioRuteoError,
    TIPOS_TRANSPORTE_QUERY,
    ValidacionTransporteError,
)
from repository.transporte_repository import transporte_repository
from service.transporte_service import TransporteService

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/transporte",
    tags=["Transporte"],
)

# Instanciar el servicio con inyección del repositorio
service = TransporteService(repo=transporte_repository)


def _respuesta_error_400(mensaje_error: str) -> JSONResponse:
    errores = [e.strip() for e in mensaje_error.split(";") if e.strip()]
    cuerpo = ErrorTransporteResponse(
        message="Parámetros de geolocalización o itinerario inválidos",
        data=ErrorTransporteDataResponse(errores=errores or [mensaje_error]),
        success=False,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=cuerpo.model_dump(),
    )


# ── GET /api/v1/transporte/rutas ──────────────────────────────
@router.get(
    "/rutas",
    response_model=RutasTransporteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "model": ErrorTransporteResponse,
            "description": "Parámetros de geolocalización o itinerario inválidos",
        },
        503: {
            "description": "Servicio de ruteo de transporte temporalmente no disponible",
        },
    },
)
def consultar_rutas_transporte(
    latitud_origen: float = Query(..., description="Coordenada WGS84 de salida (-90.0 a 90.0)"),
    longitud_origen: float = Query(..., description="Coordenada WGS84 de salida (-180.0 a 180.0)"),
    latitud_destino: float = Query(..., description="Coordenada WGS84 de llegada (-90.0 a 90.0)"),
    longitud_destino: float = Query(..., description="Coordenada WGS84 de llegada (-180.0 a 180.0)"),
    hora_salida: Optional[str] = Query(None, description="Hora programada en formato ISO 8601"),
    tipo_transporte: Optional[TIPOS_TRANSPORTE_QUERY] = Query(
        None,
        description="Filtro por modo: AUTOBUS_RAPIDO, METRO, TRANVIA, TODOS",
    ),
):
    """Retorna rutas, paradas intermedias, tarifas y horarios de transporte urbano."""
    try:
        return service.consultar_rutas(
            latitud_origen=latitud_origen,
            longitud_origen=longitud_origen,
            latitud_destino=latitud_destino,
            longitud_destino=longitud_destino,
            hora_salida=hora_salida,
            tipo_transporte=tipo_transporte,
        )
    except ValidacionTransporteError as e:
        return _respuesta_error_400(str(e))
    except ServicioRuteoError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )