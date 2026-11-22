from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from domain.vuelo import (
    BusquedaVuelosResponseSchema,
    ProveedorVuelosError,
    ValidacionVueloError,
)
from repository.vuelo_repository import vuelo_repository
from service.vuelo_service import VueloService

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/logistica/vuelos",
    tags=["Logística - Vuelos"],
)

# Instanciar el servicio con inyección del repositorio
service = VueloService(repo=vuelo_repository)


# ── GET /api/v1/logistica/vuelos/buscar ───────────────────────
@router.get("/buscar", response_model=BusquedaVuelosResponseSchema)
def buscar_vuelos(
    origen: Optional[str] = Query(
        default=None, description="Código IATA de aeropuerto de origen (3 letras)"
    ),
    destino: Optional[str] = Query(
        default=None, description="Código IATA de aeropuerto de destino (3 letras)"
    ),
    fecha_ida: Optional[str] = Query(
        default=None, description="Fecha de ida en formato YYYY-MM-DD"
    ),
    pasajeros: int = Query(
        default=1, description="Número de pasajeros (mayor o igual a 1)"
    ),
    fecha_retorno: Optional[str] = Query(
        default=None, description="Fecha de retorno opcional en formato YYYY-MM-DD"
    ),
):
    """Busca y cotiza vuelos disponibles según ruta, fechas y pasajeros."""
    if origen is None or destino is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los parámetros obligatorios origen y destino son requeridos",
        )
    try:
        return service.buscar(
            origen=origen,
            destino=destino,
            fecha_ida=fecha_ida,
            pasajeros=pasajeros,
            fecha_retorno=fecha_retorno,
        )
    except ValidacionVueloError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except ProveedorVuelosError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e