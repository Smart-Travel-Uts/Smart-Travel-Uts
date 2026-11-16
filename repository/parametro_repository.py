from domain.parametro_global import ParametroGlobal
from typing import Optional

class ParametroGlobalRepository:
    def __init__(self):
        # Almacén en memoria: lista de objetos ParametroGlobal
        self._datos: list[ParametroGlobal] = []
        
        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self):
        """Carga datos iniciales de ejemplo para los parámetros globales."""
        iniciales = [
            ParametroGlobal("distancia_max_ruta", "Md-03", "15", "INTEGER", "ACTIVO", False),
            ParametroGlobal("umbral_alerta_clima", "Md-02", "85", "INTEGER", "ACTIVO", False),
            ParametroGlobal("token_secreto_interno", "Md-01", "sk_live_9988776655", "STRING", "ACTIVO", True),
            ParametroGlobal("parametro_obsoleto", "Md-03", "10", "INTEGER", "INACTIVO", False),
        ]
        self._datos = iniciales

    def obtener_por_clave(self, clave: str) -> Optional[ParametroGlobal]:
        """Busca y retorna un parámetro global según su clave única."""
        return next((p for p in self._datos if p.clave == clave), None)

# Instancia única compartida (Singleton simple)
parametro_repository = ParametroGlobalRepository()