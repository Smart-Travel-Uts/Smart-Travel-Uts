
from fastapi import APIRouter, status, Path
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from domain.parametro_global import ParametroGlobalSuccessResponse, ParametroGlobalErrorResponse
from service.parametro_service import ParametroGlobalService
from repository.parametro_repository import parametro_repository

# Crear el router con prefijo y etiqueta para la documentación
router = APIRouter(
    prefix="/api/v1/parametricas/globales",
    tags=["Parámetros Globales"]
)

# Instanciar el servicio con inyección del repositorio
service = ParametroGlobalService(repo=parametro_repository)


# — GET /api/v1/parametricas/globales/{clave} —
@router.get(
    "/{clave}",
    response_model=ParametroGlobalSuccessResponse,
    summary="Consultar parámetro global operativo por clave",
    description="Retorna el valor y metadatos de configuración operativa de un parámetro global vigente."
)
def consultar_parametro_global(
    clave: str = Path(..., description="Clave única del parámetro global (ej. distancia_max_ruta)")
):
    """Consulta un parámetro global por su clave única validando vigencia y restricciones."""
    try:
        return service.consultar_por_clave(clave)

    except ValidationError:
            # Caso 5: Formato de clave mal formado o con caracteres inválidos -> 400 Bad Request
            error_resp = ParametroGlobalErrorResponse(
                mensaje="Formato de clave no válido",
                data={"clave": clave, "valor": None},
                success=False
            )
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error_resp.model_dump())
    
    except ValueError as e:
        # Caso 3: Clave inexistente o no vigente -> 404 Not Found
        error_resp = ParametroGlobalErrorResponse(
            mensaje=str(e),
            data={"clave": clave, "valor": None},
            success=False
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error_resp.model_dump())

    except PermissionError as e:
        # Caso 4: Parámetro marcado como interno (restringido) -> 403 Forbidden
        error_resp = ParametroGlobalErrorResponse(
            mensaje=str(e),
            data={"clave": clave, "valor": None},
            success=False
        )
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=error_resp.model_dump())

    except RuntimeError as e:
        # Caso 7: Error de infraestructura o caída de base de datos -> 503 Service Unavailable
        error_resp = ParametroGlobalErrorResponse(
            mensaje=str(e),
            data={"clave": clave, "valor": None},
            success=False
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error_resp.model_dump())

    

   