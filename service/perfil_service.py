import os
from typing import Optional

import jwt
from fastapi import HTTPException, status

from domain.perfil import (
    ActualizarPerfilRequest,
    PerfilSuccessResponse,
)
from repository.perfil_repository import PerfilRepository, perfil_repository

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "smart_travel_uts_secret_key_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class PerfilService:
    """Capa de lógica de negocio para consultar y actualizar el perfil del viajero."""

    def __init__(self, repository: PerfilRepository = perfil_repository) -> None:
        self._repository = repository

    def _extraer_usuario_id_desde_token(self, authorization_header: Optional[str]) -> str:
        """Valida la cabecera Bearer Token y decodifica el JWT del usuario autenticado."""
        if not authorization_header or not authorization_header.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "mensaje": "Cabecera de autenticación requerida",
                    "data": None,
                    "success": False,
                },
            )

        partes = authorization_header.strip().split()
        if len(partes) != 2 or partes[0].lower() != "bearer" or not partes[1].strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "mensaje": "Token de sesión no válido o expirado",
                    "data": None,
                    "success": False,
                },
            )

        token = partes[1].strip()

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "mensaje": "Token de sesión no válido o expirado",
                    "data": None,
                    "success": False,
                },
            )

        usuario_id = payload.get("sub") or payload.get("usuario_id")
        if not usuario_id or not str(usuario_id).strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "mensaje": "Token de sesión no válido o expirado",
                    "data": None,
                    "success": False,
                },
            )

        return str(usuario_id).strip()

    def consultar_perfil(self, authorization_header: Optional[str]) -> PerfilSuccessResponse:
        """Obtiene la información personal y preferencias del viajero autenticado."""
        usuario_id = self._extraer_usuario_id_desde_token(authorization_header)

        try:
            perfil = self._repository.obtener_por_usuario_id(usuario_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "mensaje": "No fue posible consultar el perfil del usuario",
                    "data": None,
                    "success": False,
                },
            )

        if perfil is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "mensaje": "Token de sesión no válido o expirado",
                    "data": None,
                    "success": False,
                },
            )

        return PerfilSuccessResponse(
            message="Consulta de perfil exitosa",
            data=perfil,
            success=True,
        )

    def actualizar_perfil(
        self,
        authorization_header: Optional[str],
        datos_actualizacion: ActualizarPerfilRequest,
    ) -> PerfilSuccessResponse:
        """Actualiza los datos personales y preferencias del viajero autenticado."""
        usuario_id = self._extraer_usuario_id_desde_token(authorization_header)

        try:
            perfil_actualizado = self._repository.actualizar_perfil(
                usuario_id=usuario_id,
                datos_actualizacion=datos_actualizacion,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "mensaje": "No fue posible actualizar el perfil del usuario",
                    "data": None,
                    "success": False,
                },
            )

        if perfil_actualizado is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "mensaje": "Token de sesión no válido o expirado",
                    "data": None,
                    "success": False,
                },
            )

        return PerfilSuccessResponse(
            message="Actualización de perfil exitosa",
            data=perfil_actualizado,
            success=True,
        )


perfil_service = PerfilService()