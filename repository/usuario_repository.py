import bcrypt
from typing import Optional
from domain.usuario import Usuario


class UsuarioRepository:
    """Repositorio en memoria con patrón Singleton para gestionar usuarios registrados."""

    def __init__(self):
        # Generamos los hashes con bcrypt al inicializar para simular contraseñas encriptadas en BD
        hash_principal = bcrypt.hashpw("ClaveSegura123!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        hash_secundario = bcrypt.hashpw("TravelPass2026*".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        self._usuarios: dict[str, Usuario] = {
            "usuario@smarttravel.com": Usuario(
                usuario_id="USR-10293",
                correo="usuario@smarttravel.com",
                password_hash=hash_principal,
                activo=True
            ),
            "admin@smarttravel.com": Usuario(
                usuario_id="USR-10001",
                correo="admin@smarttravel.com",
                password_hash=hash_secundario,
                activo=True
            )
        }

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        """Busca un usuario activo por su correo electrónico normalizado."""
        usuario = self._usuarios.get(correo.strip().lower())
        if usuario and usuario.activo:
            return usuario
        return None


# Instancia Singleton exportada para inyección en la capa de servicio
usuario_repository = UsuarioRepository()