from repository.catalogo_repository import CatalogoRepository

class CatalogoService:
    def __init__(self, repo: CatalogoRepository):
        self.repo = repo

    def consultar_catalogo(self, tipo_catalogo: str) -> dict:
        tipo_limpio = tipo_catalogo.strip().upper()
        items = self.repo.obtener_por_tipo(tipo_limpio)
        
        # Si no existen datos o el catálogo no está registrado
        if not items:
            return {
                "mensaje": "El catálogo solicitado no existe o se encuentra deshabilitado",
                "data": {
                    "tipo_catalogo": tipo_limpio,
                    "total_items": 0,
                    "items": []
                },
                "success": False
            }
        
        # Si la consulta es exitosa
        return {
            "message": "Consulta de catálogo maestro exitosa",
            "data": {
                "tipo_catalogo": tipo_limpio,
                "total_items": len(items),
                "items": items
            },
            "success": True
        }