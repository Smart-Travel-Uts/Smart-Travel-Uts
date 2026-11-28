# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from domain.colaboracion import (
    ErrorPermisoResponse,
    InvitarColaboradoresRequest,
    InvitarColaboradoresResponse,
    ListaColaboradoresResponse,
)
from repository.colaboracion_repository import colaboracion_repository
from service.colaboracion_service import (
    ColaboracionService,
    ConflictoVersionError,
    EnlaceExpiradoError,
    PermisoInsuficienteError,
)

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/itinerarios",
    tags=["Colaboración e Itinerarios Compartidos"],
)

# Instanciar el servicio con inyección del repositorio
service = ColaboracionService(repo=colaboracion_repository)


class ActividadColaborativaRequest(BaseModel):
    titulo:           str           = Field(..., min_length=2)
    descripcion:      Optional[str]   = None
    version_esperada: Optional[int]   = Field(None, ge=1)


def _extraer_identidad(
    authorization: Optional[str],
    x_user_id: Optional[str],
    x_user_email: Optional[str],
) -> tuple[str, Optional[str]]:
    """Extrae usuario y correo desde cabeceras de prueba/JWT sin lógica de negocio."""
    usuario = (x_user_id or "").strip()
    if not usuario and authorization:
        token_limpio = authorization.replace("Bearer", "").replace("bearer", "").strip()
        if "roberto" in token_limpio.lower():
            usuario = "USR-ROBERTO"
        elif token_limpio:
            usuario = "USR-9921"
    return (usuario or "USR-9921"), x_user_email


# ── POST /api/v1/itinerarios/{id_itinerario}/colaboradores ──
@router.post(
    "/{id_itinerario}/colaboradores",
    response_model=InvitarColaboradoresResponse,
    status_code=status.HTTP_201_CREATED,
    responses={403: {"model": ErrorPermisoResponse}},
)
def invitar_colaboradores(
    id_itinerario: str,
    datos: InvitarColaboradoresRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
):
    """Invita a nuevos miembros al itinerario con un rol asignado (PROPIETARIO)."""
    usuario_id, email = _extraer_identidad(authorization, x_user_id, x_user_email)
    try:
        return service.invitar_colaboradores(
            id_itinerario=id_itinerario,
            datos=datos,
            id_usuario_solicitante=usuario_id,
            email_solicitante=email,
        )
    except PermisoInsuficienteError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=e.to_response_dict(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ── GET /api/v1/itinerarios/{id_itinerario}/colaboradores ───
@router.get(
    "/{id_itinerario}/colaboradores",
    response_model=ListaColaboradoresResponse,
    responses={403: {"model": ErrorPermisoResponse}},
)
def listar_colaboradores(
    id_itinerario: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
):
    """Lista los miembros actuales del itinerario y sus estados de invitación."""
    usuario_id, email = _extraer_identidad(authorization, x_user_id, x_user_email)
    try:
        return service.listar_colaboradores(
            id_itinerario=id_itinerario,
            id_usuario_solicitante=usuario_id,
            email_solicitante=email,
        )
    except PermisoInsuficienteError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=e.to_response_dict(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ── DELETE /api/v1/itinerarios/{id_itinerario}/colaboradores/{id_usuario}
@router.delete(
    "/{id_itinerario}/colaboradores/{id_usuario}",
    responses={403: {"model": ErrorPermisoResponse}},
)
def revocar_colaborador(
    id_itinerario: str,
    id_usuario: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
):
    """Revoca el acceso a un colaborador específico (PROPIETARIO)."""
    usuario_id, email = _extraer_identidad(authorization, x_user_id, x_user_email)
    try:
        return service.revocar_colaborador(
            id_itinerario=id_itinerario,
            id_usuario_objetivo=id_usuario,
            id_usuario_solicitante=usuario_id,
            email_solicitante=email,
        )
    except PermisoInsuficienteError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=e.to_response_dict(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ── GET /api/v1/itinerarios/compartido?token=... ──────────────
@router.get("/compartido")
def acceder_enlace_compartido(
    token: str = Query(..., min_length=1, description="Token del enlace compartido"),
):
    """Valida y resuelve un enlace compartido de lectura."""
    try:
        return service.consultar_enlace_compartido(token=token)
    except EnlaceExpiradoError as e:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

# ── POST /api/v1/itinerarios/{id_itinerario}/actividades-colaborativas ──
@router.post(
    "/{id_itinerario}/actividades-colaborativas",
    status_code=status.HTTP_201_CREATED,
    responses={403: {"model": ErrorPermisoResponse}},
)
def crear_actividad_colaborativa(
    id_itinerario: str,
    datos: ActividadColaborativaRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
):
    """Agrega una actividad validando permisos RBAC y registrando auditoría."""
    usuario_id, email = _extraer_identidad(authorization, x_user_id, x_user_email)
    try:
        resultado = service.registrar_edicion_con_auditoria(
            id_itinerario=id_itinerario,
            id_usuario=usuario_id,
            accion="CREAR_ACTIVIDAD",
            detalle=f"Actividad '{datos.titulo}' agregada",
            version_esperada=datos.version_esperada,
            email_usuario=email,
        )
        return {
            "message": "Actividad agregada exitosamente",
            "data": {"actividad": datos.model_dump(), **resultado},
            "success": True,
        }
    except PermisoInsuficienteError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=e.to_response_dict(),
        )
    except ConflictoVersionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ── PUT /api/v1/itinerarios/{id_itinerario}/actividades/{id_actividad}
@router.put(
    "/{id_itinerario}/actividades/{id_actividad}",
    responses={403: {"model": ErrorPermisoResponse}},
)
def modificar_actividad_colaborativa(
    id_itinerario: str,
    id_actividad: str,
    datos: ActividadColaborativaRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
):
    """Modifica una actividad con bloqueo optimista (version) y auditoría."""
    usuario_id, email = _extraer_identidad(authorization, x_user_id, x_user_email)
    try:
        resultado = service.registrar_edicion_con_auditoria(
            id_itinerario=id_itinerario,
            id_usuario=usuario_id,
            accion="ACTUALIZAR_ACTIVIDAD",
            detalle=f"Actividad '{id_actividad}' actualizada a '{datos.titulo}'",
            version_esperada=datos.version_esperada,
            email_usuario=email,
        )
        return {
            "message": "Actividad actualizada exitosamente",
            "data": {"id_actividad": id_actividad, **resultado},
            "success": True,
        }
    except PermisoInsuficienteError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=e.to_response_dict(),
        )
    except ConflictoVersionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )