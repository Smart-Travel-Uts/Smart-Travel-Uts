from domain.regla_comercial import ReglaComercialQuery, ReglaComercialSuccessResponse, ReglaComercialDataResponse
from repository.regla_comercial_repository import ReglaComercialRepository


class ReglaComercialService:
    def __init__(self, repo: ReglaComercialRepository):
        self.repo = repo

    def consultar_por_tipo_servicio(self, tipo_servicio: str | None) -> ReglaComercialSuccessResponse:
        # 1. Caso 4: Validar si el parámetro obligatorio fue omitido o viene vacío
        if tipo_servicio is None or not tipo_servicio.strip():
            raise KeyError("El parámetro tipo_servicio es obligatorio")

        # 2. Caso 5: Validar formato alfanumérico mediante el esquema Pydantic
        # Si tiene caracteres especiales (ej. ALOJ%&123), lanza ValidationError
        query = ReglaComercialQuery(tipo_servicio=tipo_servicio)

        # 3. Caso 6: Consultar al repositorio capturando fallos de infraestructura/BD
        try:
            regla = self.repo.obtener_por_tipo_servicio(query.tipo_servicio)
        except Exception as e:
            raise RuntimeError("No fue posible consultar las reglas comerciales") from e

        # 4. Caso 3: Validar existencia y estado activo
        if not regla or not regla.es_vigente():
            raise ValueError("El tipo de servicio especificado no cuenta con reglas comerciales activas")

        # 5. Casos 1 y 2: Construir y retornar la respuesta exitosa
        return ReglaComercialSuccessResponse(
            message="Consulta de reglas comerciales exitosa",
            data=ReglaComercialDataResponse(**regla.to_response()),
            success=True
        )