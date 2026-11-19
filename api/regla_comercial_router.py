from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Optional
from domain.regla_comercial import ReglaComercialSuccessResponse, ReglaComercialErrorResponse
from service.regla_comercial_service import ReglaComercialService
from repository.regla_comercial_repository import regla_comercial_repository

router = APIRouter(
    prefix="/api/v1/parametricas/reglas-comerciales",
    tags=["Reglas Comerciales"]
)

service = ReglaComercialService(repo=regla_comercial_repository)


@router.get(
    "",
    response_model=ReglaComercialSuccessResponse,
    summary="Consultar reglas comerciales, comisiones y políticas de cancelación",
    description="Retorna el esquema de comisiones freemium y tramos de cancelación vigentes según el tipo de servicio."
)
def consultar_reglas_comerciales(
    tipo_servicio: Optional[str] = Query(
        default=None,
        description="Tipo de servicio a consultar (ej. ALOJAMIENTO, VUELO, EVENTO)"
    )
):
    valor_actual = tipo_servicio if tipo_servicio is not None else ""

    try:
        return service.consultar_por_tipo_servicio(tipo_servicio)

    except KeyError:
        # Caso 4: Parámetro tipo_servicio omitido o vacío -> 400 Bad Request
        error_resp = ReglaComercialErrorResponse(
            mensaje="El parámetro tipo_servicio es obligatorio",
            data={"tipo_servicio": valor_actual, "porcentaje_comision_freemium": 0, "politica_cancelacion": None},
            success=False
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error_resp.model_dump())

    except ValidationError:
        # Caso 5: Caracteres especiales no válidos (ej. ALOJ%&123) -> 400 Bad Request
        error_resp = ReglaComercialErrorResponse(
            mensaje="Formato de tipo de servicio no válido",
            data={"tipo_servicio": valor_actual, "porcentaje_comision_freemium": 0, "politica_cancelacion": None},
            success=False
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error_resp.model_dump())

    except ValueError as e:
        # Caso 3: Tipo de servicio inexistente o inactivo -> 404 Not Found
        error_resp = ReglaComercialErrorResponse(
            mensaje=str(e),
            data={"tipo_servicio": valor_actual.upper(), "porcentaje_comision_freemium": 0, "politica_cancelacion": None},
            success=False
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error_resp.model_dump())

    except RuntimeError as e:
        # Caso 6: Fallo en base de datos -> 503 Service Unavailable
        error_resp = ReglaComercialErrorResponse(
            mensaje=str(e),
            data={"tipo_servicio": valor_actual.upper(), "porcentaje_comision_freemium": 0, "politica_cancelacion": None},
            success=False
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error_resp.model_dump())