from fastapi import APIRouter, status, Response
from service.catalogo_service import CatalogoService
from repository.catalogo_repository import catalogo_repository
from domain.catalogo import CatalogoInputValidation

router = APIRouter(
    prefix="/api/v1/parametricas/catalogos",
    tags=["Catálogos Maestros"]
)

# Inyección de dependencias del repositorio hacia el servicio
service = CatalogoService(repo=catalogo_repository)

@router.get("/{tipo_catalogo}")
def consultar_catalogo_maestro(tipo_catalogo: str, response: Response):
    """
    Endpoint para consultar el catálogo maestro por su tipo (HU-01).
    """
    try:
        # Validación en la entrada usando el schema de dominio
        validador = CatalogoInputValidation(tipo_catalogo=tipo_catalogo)
        tipo_validado = validador.tipo_catalogo
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "mensaje": str(e),
            "data": None,
            "success": False
        }

    # Ejecutar lógica del servicio
    resultado = service.consultar_catalogo(tipo_validado)
    
    # Asignar código HTTP según el resultado de negocio
    if not resultado["success"]:
        response.status_code = status.HTTP_404_NOT_FOUND
    else:
        response.status_code = status.HTTP_200_OK
        
    return resultado