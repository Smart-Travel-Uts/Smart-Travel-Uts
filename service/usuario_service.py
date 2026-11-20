import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from domain.usuario import (
    AutenticacionRequest,
    AutenticacionSuccessResponse,
    TokenData
)
from repository.usuario_repository import UsuarioRepository


class UsuarioService:
    """Capa de servicio con lógica de negocio para autenticación y emisión de tokens JWT."""

    SECRET_KEY = "smart_travel_uts_secret_key_2026"
    ALGORITHM = "HS256"
    EXPIRACION_SEGUNDOS = 3600

    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def autenticar_usuario(self, correo: str, contrasena: str) -> AutenticacionSuccessResponse:
        # 1. Validación de entrada mediante el esquema Pydantic del dominio (Casos 4 y 5)
        datos_validados = AutenticacionRequest(correo=correo, contrasena=contrasena)

        # 2. Consulta al repositorio con captura de fallos de conexión (Caso 6 -> 503)
        try:
            usuario = self.repo.obtener_por_correo(datos_validados.correo)
        except Exception as e:
            raise RuntimeError("No fue posible autenticar al usuario") from e

        # 3. Verificación de existencia del usuario (Caso 3 -> 401)
        if not usuario:
            raise PermissionError("Credenciales de acceso no válidas")

        # 4. Verificación de contraseña encriptada con bcrypt (Caso 2 -> 401)
        contrasena_valida = bcrypt.checkpw(
            datos_validados.contrasena.encode("utf-8"),
            usuario.password_hash.encode("utf-8")
        )
        if not contrasena_valida:
            raise PermissionError("Credenciales de acceso no válidas")

        # 5. Generación de token de acceso JWT y token de refresco (Caso 1 -> 200)
        ahora = datetime.now(timezone.utc)
        payload = {
            "sub": usuario.usuario_id,
            "email": usuario.correo,
            "iat": ahora,
            "exp": ahora + timedelta(seconds=self.EXPIRACION_SEGUNDOS)
        }
        token_acceso = jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
        token_refresco = str(uuid.uuid4())

        return AutenticacionSuccessResponse(
            message="Autenticación exitosa",
            data=TokenData(
                usuario_id=usuario.usuario_id,
                token_acceso=token_acceso,
                token_refresco=token_refresco,
                expiracion_segundos=self.EXPIRACION_SEGUNDOS
            ),
            success=True
        )