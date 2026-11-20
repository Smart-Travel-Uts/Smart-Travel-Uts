import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Usuario(BaseModel):
    """Entidad de dominio que representa un usuario registrado en el sistema."""
    usuario_id: str
    correo: str
    password_hash: str
    activo: bool = True


class AutenticacionRequest(BaseModel):
    """Esquema de entrada para la solicitud de inicio de sesión (POST)."""
    correo: Optional[str] = Field(default=None, description="Correo electrónico del usuario")
    contrasena: Optional[str] = Field(default=None, description="Contraseña en texto plano")

    @field_validator("correo")
    @classmethod
    def validar_formato_correo(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            raise KeyError("El campo correo es obligatorio")
        correo_limpio = v.strip().lower()
        # Caso 4: Validar formato de correo electrónico
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", correo_limpio):
            raise ValueError("Formato de correo electrónico no válido")
        return correo_limpio

    @field_validator("contrasena")
    @classmethod
    def validar_contrasena_obligatoria(cls, v: Optional[str]) -> Optional[str]:
        # Caso 5: Validar que la contraseña no venga vacía u omitida
        if v is None or not v.strip():
            raise KeyError("El campo contraseña es obligatorio")
        return v


class TokenData(BaseModel):
    """Estructura interna 'data' para la respuesta exitosa de autenticación."""
    usuario_id: str
    token_acceso: str
    token_refresco: str
    expiracion_segundos: int


class AutenticacionSuccessResponse(BaseModel):
    """Estructura JSON para respuesta HTTP 200 OK."""
    message: str = "Autenticación exitosa"
    data: TokenData
    success: bool = True


class AutenticacionErrorResponse(BaseModel):
    """Estructura JSON para respuestas de error (400, 401, 503)."""
    mensaje: str
    data: Optional[dict] = None
    success: bool = False