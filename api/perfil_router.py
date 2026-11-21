from typing import Optional

from fastapi import APIRouter, Depends, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domain.perfil import (
    ActualizarPerfilRequest,
    PerfilErrorResponse,
    PerfilSuccessResponse,
)
from service.perfil_service import PerfilService, perfil_service

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Perfil y Preferencias del Viajero"],
)

security_scheme = HTTPBearer(auto_error=False)


def obtener_cabecera_autorizacion(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    authorization: Optional[str] = Header(default=None),
) -> Optional[str]:
    """Permite recibir el token desde el botón Authorize de Swagger o como cabecera Authorization."""
    if credentials and credentials.credentials:
        return f"{credentials.scheme} {credentials.credentials}"
    return authorization


@router.get(
    "/perfil",
    response_model=PerfilSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar perfil y preferencias del viajero",
    description=(
        "Valida el token JWT enviado en la cabecera Authorization (Bearer Token) "
        "y retorna los datos personales junto con las preferencias del viajero."
    ),
    responses={
        200: {
            "model": PerfilSuccessResponse,
            "description": "Consulta de perfil exitosa",
        },
        401: {
            "model": PerfilErrorResponse,
            "description": "Cabecera de autenticación requerida o token JWT no válido/expirado",
        },
        503: {
            "model": PerfilErrorResponse,
            "description": "Error de conexión con la base de datos de usuarios",
        },
    },
)
def consultar_perfil(
    auth_header: Optional[str] = Depends(obtener_cabecera_autorizacion),
    service: PerfilService = Depends(lambda: perfil_service),
) -> PerfilSuccessResponse:
    """Endpoint GET /api/v1/usuarios/perfil para consultar datos y preferencias."""
    return service.consultar_perfil(auth_header)


@router.put(
    "/perfil",
    response_model=PerfilSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar perfil y preferencias del viajero",
    description=(
        "Valida el token JWT y actualiza el nombre completo, idioma preferido, "
        "moneda base y categorías de interés del viajero autenticado."
    ),
    responses={
        200: {
            "model": PerfilSuccessResponse,
            "description": "Actualización de perfil exitosa",
        },
        400: {
            "model": PerfilErrorResponse,
            "description": "Datos de actualización no válidos (ej. moneda o idioma fuera del catálogo)",
        },
        401: {
            "model": PerfilErrorResponse,
            "description": "Cabecera de autenticación requerida o token JWT no válido/expirado",
        },
        503: {
            "model": PerfilErrorResponse,
            "description": "Error de conexión con la base de datos de usuarios",
        },
    },
)
def actualizar_perfil(
    request: ActualizarPerfilRequest,
    auth_header: Optional[str] = Depends(obtener_cabecera_autorizacion),
    service: PerfilService = Depends(lambda: perfil_service),
) -> PerfilSuccessResponse:
    """Endpoint PUT /api/v1/usuarios/perfil para actualizar datos y preferencias."""
    return service.actualizar_perfil(
        authorization_header=auth_header,
        datos_actualizacion=request,
    )