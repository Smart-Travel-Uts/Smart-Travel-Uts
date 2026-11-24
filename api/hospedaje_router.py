# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from domain.hospedaje import (
    AlojamientoNoEncontradoError,
    BusquedaHospedajeResponse,
    DisponibilidadHospedajeResponse,
    ErrorHospedajeDataResponse,
    ErrorHospedajeResponse,
    ProveedorHospedajeError,
    ValidacionHospedajeError,
)
from repository.hospedaje_repository import hospedaje_repository
from service.hospedaje_service import HospedajeService

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/hospedaje",
    tags=["Hospedaje"],
)

# Instanciar el servicio con inyección del repositorio
service = HospedajeService(repo=hospedaje_repository)


def _respuesta_error_400(mensaje_error: str) -> JSONResponse:
    cuerpo = ErrorHospedajeResponse(
        message="Error en los parámetros de consulta de hospedaje",
        data=ErrorHospedajeDataResponse(errores=[mensaje_error]),
        success=False,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=cuerpo.model_dump(),
    )


# ── GET /api/v1/hospedaje/buscar ──────────────────────────────
@router.get(
    "/buscar",
    response_model=BusquedaHospedajeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorHospedajeResponse, "description": "Parámetros de búsqueda inválidos"},
        503: {"description": "Servicio de hospedaje no disponible"},
    },
)
def buscar_alojamientos(
    destino: str = Query(..., description="Ciudad o destino"),
    fecha_entrada: date = Query(..., description="Fecha de entrada (YYYY-MM-DD)"),
    fecha_salida: date = Query(..., description="Fecha de salida (YYYY-MM-DD)"),
    huespedes: int = Query(1, description="Cantidad de huéspedes"),
    precio_min: Optional[float] = Query(None, description="Precio mínimo por noche"),
    precio_max: Optional[float] = Query(None, description="Precio máximo por noche"),
    calificacion_min: Optional[float] = Query(None, description="Calificación mínima"),
):
    """Busca y filtra alojamientos disponibles según destino, fechas, huéspedes y preferencias."""
    try:
        return service.buscar(
            destino=destino,
            fecha_entrada=fecha_entrada,
            fecha_salida=fecha_salida,
            huespedes=huespedes,
            precio_min=precio_min,
            precio_max=precio_max,
            calificacion_min=calificacion_min,
        )
    except ValidacionHospedajeError as e:
        return _respuesta_error_400(str(e))
    except ProveedorHospedajeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


# ── GET /api/v1/hospedaje/{id_alojamiento}/disponibilidad ──
@router.get(
    "/{id_alojamiento}/disponibilidad",
    response_model=DisponibilidadHospedajeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorHospedajeResponse, "description": "Parámetros de disponibilidad inválidos"},
        404: {"description": "Alojamiento inexistente o sin disponibilidad"},
        503: {"description": "Servicio de hospedaje no disponible"},
    },
)
def consultar_disponibilidad_alojamiento(
    id_alojamiento: str,
    fecha_entrada: date = Query(..., description="Fecha de entrada (YYYY-MM-DD)"),
    fecha_salida: date = Query(..., description="Fecha de salida (YYYY-MM-DD)"),
    huespedes: int = Query(..., description="Cantidad de huéspedes"),
):
    """Verifica disponibilidad real, calcula tarifa con comisión e informa políticas del alojamiento."""
    try:
        return service.consultar_disponibilidad(
            id_alojamiento=id_alojamiento,
            fecha_entrada=fecha_entrada,
            fecha_salida=fecha_salida,
            huespedes=huespedes,
        )
    except ValidacionHospedajeError as e:
        return _respuesta_error_400(str(e))
    except AlojamientoNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ProveedorHospedajeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )