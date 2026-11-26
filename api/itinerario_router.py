# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from domain.itinerario import (
    AccesoDenegadoItinerarioError,
    ActividadCreate,
    ActividadResponse,
    AutenticacionItinerarioError,
    ErrorItinerarioResponse,
    ItinerarioCreadoDataResponse,
    ItinerarioCreadoResponse,
    ItinerarioCreate,
    ItinerarioDetalleResponse,
    ItinerarioNoEncontradoError,
    ValidacionItinerarioError,
)
from repository.itinerario_repository import itinerario_repository
from service.itinerario_service import ItinerarioService

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/itinerarios",
    tags=["Itinerarios"],
)

# Esquema Bearer para activar el botón "Authorize" en Swagger UI
security_scheme = HTTPBearer(auto_error=False)

# Instanciar el servicio con inyección del repositorio
service = ItinerarioService(repo=itinerario_repository)


def _construir_header_auth(
    credenciales: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    if not credenciales:
        return None
    esquema = credenciales.scheme or "Bearer"
    return f"{esquema} {credenciales.credentials}".strip()


# ── GET /api/v1/itinerarios ───────────────────────────────────
@router.get("/", response_model=list[ItinerarioCreadoDataResponse])
def listar_itinerarios(
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """Retorna los itinerarios del usuario autenticado."""
    try:
        return service.listar(authorization=_construir_header_auth(credenciales))
    except AutenticacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ── GET /api/v1/itinerarios/{id_itinerario} ───────────────────
@router.get(
    "/{id_itinerario}",
    response_model=ItinerarioDetalleResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorItinerarioResponse},
        403: {"model": ErrorItinerarioResponse},
        404: {"model": ErrorItinerarioResponse},
    },
)
def obtener_itinerario(
    id_itinerario: str,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """Retorna la vista consolidada por días y costos de un itinerario."""
    try:
        return service.obtener(
            id_itinerario=id_itinerario,
            authorization=_construir_header_auth(credenciales),
        )
    except AutenticacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AccesoDenegadoItinerarioError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": str(e),
                "data": None,
                "success": False,
            },
        )
    except ItinerarioNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ── POST /api/v1/itinerarios ──────────────────────────────────
@router.post(
    "/",
    response_model=ItinerarioCreadoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorItinerarioResponse},
        401: {"model": ErrorItinerarioResponse},
    },
)
def crear_itinerario(
    datos: ItinerarioCreate,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """Crea un nuevo itinerario. El cuerpo se valida automáticamente."""
    try:
        return service.crear(
            datos=datos,
            authorization=_construir_header_auth(credenciales),
        )
    except AutenticacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except ValidacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── PUT /api/v1/itinerarios/{id_itinerario} ───────────────────
@router.put("/{id_itinerario}", response_model=ItinerarioCreadoResponse)
def actualizar_itinerario(
    id_itinerario: str,
    datos: ItinerarioCreate,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """Actualiza los datos generales de un itinerario."""
    try:
        return service.actualizar(
            id_itinerario=id_itinerario,
            datos=datos,
            authorization=_construir_header_auth(credenciales),
        )
    except AutenticacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AccesoDenegadoItinerarioError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": str(e),
                "data": None,
                "success": False,
            },
        )
    except ItinerarioNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── DELETE /api/v1/itinerarios/{id_itinerario} ────────────────
@router.delete("/{id_itinerario}")
def eliminar_itinerario(
    id_itinerario: str,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """Elimina un itinerario por ID."""
    try:
        return service.eliminar(
            id_itinerario=id_itinerario,
            authorization=_construir_header_auth(credenciales),
        )
    except AutenticacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AccesoDenegadoItinerarioError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": str(e),
                "data": None,
                "success": False,
            },
        )
    except ItinerarioNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ── POST /api/v1/itinerarios/{id_itinerario}/actividades ──────
@router.post(
    "/{id_itinerario}/actividades",
    response_model=ActividadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorItinerarioResponse},
        401: {"model": ErrorItinerarioResponse},
        403: {"model": ErrorItinerarioResponse},
        404: {"model": ErrorItinerarioResponse},
    },
)
def agregar_actividad(
    id_itinerario: str,
    datos: ActividadCreate,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """Agrega una actividad al cronograma del itinerario."""
    try:
        return service.agregar_actividad(
            id_itinerario=id_itinerario,
            datos=datos,
            authorization=_construir_header_auth(credenciales),
        )
    except AutenticacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AccesoDenegadoItinerarioError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": str(e),
                "data": None,
                "success": False,
            },
        )
    except ItinerarioNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── DELETE /api/v1/itinerarios/{id_itinerario}/actividades/{id_actividad} ──
@router.delete("/{id_itinerario}/actividades/{id_actividad}")
def eliminar_actividad(
    id_itinerario: str,
    id_actividad: str,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """Elimina una actividad del itinerario."""
    try:
        return service.eliminar_actividad(
            id_itinerario=id_itinerario,
            id_actividad=id_actividad,
            authorization=_construir_header_auth(credenciales),
        )
    except AutenticacionItinerarioError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except AccesoDenegadoItinerarioError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": str(e),
                "data": None,
                "success": False,
            },
        )
    except ItinerarioNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )