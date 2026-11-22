import os
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError

from domain.notificacion import (
    HistorialNotificacionesResponse,
    NotificacionRepositorioError,
)
from service.notificacion_service import NotificacionService

router = APIRouter(
    prefix="/api/v1/notificaciones",
    tags=["Notificaciones"],
)

security = HTTPBearer(auto_error=False)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "smart_travel_uts_secret_key_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

_notificacion_service = NotificacionService()


def obtener_usuario_autenticado(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
        )

    token = credentials.credentials.strip()
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        usuario_id = (
            payload.get("sub")
            or payload.get("usuario_id")
            or payload.get("id")
            or payload.get("user_id")
        )
        if not usuario_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticación requerida",
            )
        return str(usuario_id)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
        )


@router.get(
    "/historial",
    response_model=HistorialNotificacionesResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_historial_notificaciones(
    request: Request,
    usuario_id: str = Depends(obtener_usuario_autenticado),
) -> HistorialNotificacionesResponse:
    service: NotificacionService = getattr(
        request.app.state, "notificacion_service", _notificacion_service
    )
    try:
        return service.obtener_historial(usuario_id)
    except NotificacionRepositorioError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "No fue posible obtener el historial de notificaciones",
        )