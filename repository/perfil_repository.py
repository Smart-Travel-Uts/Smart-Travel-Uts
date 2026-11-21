from threading import Lock
from typing import Dict, Optional

from domain.perfil import (
    ActualizarPerfilRequest,
    PerfilUsuario,
    PreferenciasViajero,
)


class PerfilRepository:
    """Repositorio en memoria con patrón Singleton para gestionar perfiles y preferencias."""

    _instance: Optional["PerfilRepository"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "PerfilRepository":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._inicializar_datos()
        return cls._instance

    def _inicializar_datos(self) -> None:
        """Inicializa perfiles de prueba alineados con los datos esperados en la HU-05."""
        self._perfiles_por_id: Dict[str, PerfilUsuario] = {
            "USR-10293": PerfilUsuario(
                usuario_id="USR-10293",
                nombre_completo="Carlos Mendoza",
                correo="carlos@email.com",
                preferencias=PreferenciasViajero(
                    idioma="ES",
                    moneda_base="USD",
                    categorias_interes=["GASTRONOMIA", "PLAYA"],
                ),
            ),
            "USR-20481": PerfilUsuario(
                usuario_id="USR-20481",
                nombre_completo="Samuel González",
                correo="usuario@smarttravel.com",
                preferencias=PreferenciasViajero(
                    idioma="ES",
                    moneda_base="COP",
                    categorias_interes=["AVENTURA", "CULTURA"],
                ),
            ),
        }

    def obtener_por_usuario_id(self, usuario_id: str) -> Optional[PerfilUsuario]:
        """Recupera el perfil del viajero por su identificador de usuario."""
        if not usuario_id or not usuario_id.strip():
            return None
        return self._perfiles_por_id.get(usuario_id.strip())

    def actualizar_perfil(
        self,
        usuario_id: str,
        datos_actualizacion: ActualizarPerfilRequest,
    ) -> Optional[PerfilUsuario]:
        """Actualiza los datos personales y preferencias del viajero si existe."""
        perfil_actual = self.obtener_por_usuario_id(usuario_id)
        if perfil_actual is None:
            return None

        nuevo_nombre = (
            datos_actualizacion.nombre_completo
            if datos_actualizacion.nombre_completo is not None
            else perfil_actual.nombre_completo
        )

        nuevo_idioma = (
            datos_actualizacion.idioma
            if datos_actualizacion.idioma is not None
            else perfil_actual.preferencias.idioma
        )

        nueva_moneda = (
            datos_actualizacion.moneda_base
            if datos_actualizacion.moneda_base is not None
            else perfil_actual.preferencias.moneda_base
        )

        nuevas_categorias = (
            datos_actualizacion.categorias_interes
            if datos_actualizacion.categorias_interes is not None
            else list(perfil_actual.preferencias.categorias_interes)
        )

        perfil_actualizado = PerfilUsuario(
            usuario_id=perfil_actual.usuario_id,
            nombre_completo=nuevo_nombre,
            correo=perfil_actual.correo,
            preferencias=PreferenciasViajero(
                idioma=nuevo_idioma,
                moneda_base=nueva_moneda,
                categorias_interes=nuevas_categorias,
            ),
        )

        self._perfiles_por_id[perfil_actual.usuario_id] = perfil_actualizado
        return perfil_actualizado


perfil_repository = PerfilRepository()