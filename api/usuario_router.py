from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from domain.usuario import (
    AutenticacionSuccessResponse,
    AutenticacionErrorResponse
)
from repository.usuario_repository import usuario_repository
from service.usuario_service import UsuarioService

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios y Autenticación"]
)

# Instancia del servicio inyectando el repositorio Singleton
usuario_service = UsuarioService(repo=usuario_repository)


class AutenticacionPayload(BaseModel):
    """Cuerpo JSON que aparecerá prellenado en Swagger UI para facilitar las pruebas."""
    correo: Optional[str] = Field(
        default="usuario@smarttravel.com",
        description="Correo electrónico registrado"
    )
    contrasena: Optional[str] = Field(
        default="ClaveSegura123!",
        description="Contraseña del usuario"
    )


@router.post(
    "/autenticar",
    response_model=AutenticacionSuccessResponse,
    summary="Autenticar usuario y generar tokens JWT",
    description="Valida las credenciales de acceso (correo y contraseña) y retorna el token de acceso JWT y token de refresco.",
    responses={
        200: {"model": AutenticacionSuccessResponse, "description": "Autenticación exitosa"},
        400: {"model": AutenticacionErrorResponse, "description": "Formato de correo inválido o campos obligatorios vacíos"},
        401: {"model": AutenticacionErrorResponse, "description": "Credenciales de acceso no válidas"},
        503: {"model": AutenticacionErrorResponse, "description": "Fallo en la base de datos de usuarios"}
    }
)
def autenticar_usuario(payload: AutenticacionPayload = Body(...)):
    try:
        resultado = usuario_service.autenticar_usuario(
            correo=payload.correo,
            contrasena=payload.contrasena
        )
        return resultado

    except KeyError as e:
        # Caso 5: Campo obligatorio vacío u omitido ("El campo contraseña es obligatorio")
        mensaje_error = e.args[0] if e.args else "Campo obligatorio vacío"
        error_resp = AutenticacionErrorResponse(
            mensaje=mensaje_error,
            data=None,
            success=False
        )
        return JSONResponse(status_code=400, content=error_resp.model_dump())

    except ValidationError as e:
        # Casos 4 y 5: Error de validación de Pydantic en correo o contraseña
        errores = e.errors()
        mensaje_error = "Datos de solicitud no válidos"
        if errores:
            msg_original = errores[0].get("msg", "")
            if "El campo contraseña es obligatorio" in msg_original:
                mensaje_error = "El campo contraseña es obligatorio"
            elif "El campo correo es obligatorio" in msg_original:
                mensaje_error = "El campo correo es obligatorio"
            elif "Formato de correo electrónico no válido" in msg_original:
                mensaje_error = "Formato de correo electrónico no válido"

        error_resp = AutenticacionErrorResponse(
            mensaje=mensaje_error,
            data=None,
            success=False
        )
        return JSONResponse(status_code=400, content=error_resp.model_dump())

    except PermissionError as e:
        # Casos 2 y 3: Contraseña incorrecta o usuario no registrado
        error_resp = AutenticacionErrorResponse(
            mensaje=str(e),
            data=None,
            success=False
        )
        return JSONResponse(status_code=401, content=error_resp.model_dump())

    except RuntimeError as e:
        # Caso 6: Caída de la base de datos de usuarios
        error_resp = AutenticacionErrorResponse(
            mensaje=str(e),
            data=None,
            success=False
        )
        return JSONResponse(status_code=503, content=error_resp.model_dump())