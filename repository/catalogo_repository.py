from typing import Dict, List

class CatalogoRepository:
    def __init__(self):
        # Datos semilla iniciales para los catálogos del sistema
        self._catalogos: Dict[str, List[dict]] = {
            "MONEDAS": [
                {"codigo": "USD", "descripcion": "Dólar estadounidense", "estado": "ACTIVO"},
                {"codigo": "COP", "descripcion": "Peso colombiano", "estado": "ACTIVO"}
            ],
            "PAISES": [
                {"codigo": "CO", "descripcion": "Colombia", "estado": "ACTIVO"},
                {"codigo": "US", "descripcion": "Estados Unidos", "estado": "ACTIVO"}
            ]
        }

    def obtener_por_tipo(self, tipo_catalogo: str) -> List[dict]:
        """Consulta los ítems asociados a un tipo de catálogo en mayúsculas."""
        tipo_upper = tipo_catalogo.strip().upper()
        return self._catalogos.get(tipo_upper, [])

# Instancia única para inyección de dependencias
catalogo_repository = CatalogoRepository()