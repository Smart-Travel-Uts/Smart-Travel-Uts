from domain.parametro_global import ParametroGlobalQuery, ParametroGlobalDataResponse, ParametroGlobalSuccessResponse
from repository.parametro_repository import ParametroGlobalRepository
from typing import Optional

class ParametroGlobalService:
    def __init__(self, repo: ParametroGlobalRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def consultar_por_clave(self, clave: str) -> ParametroGlobalSuccessResponse:
        # 1. Validar formato de entrada usando el schema de dominio
        query = ParametroGlobalQuery(clave=clave)

        # 2. Consultar el repositorio
        try:
            p = self.repo.obtener_por_clave(query.clave)
        except Exception:
            raise RuntimeError("No fue posible consultar el parámetro global")

        # 3. Validar existencia o vigencia
        if not p or not p.es_vigente():
            raise ValueError("El parámetro global solicitado no existe o no se encuentra vigente")

        # 4. Validar restricciones de visibilidad interna (Caso 4)
        if not p.es_publico():
            raise PermissionError("El parámetro solicitado no está disponible para consulta externa")

        # 5. Retornar respuesta estructurada conforme al contrato
        data_response = ParametroGlobalDataResponse(**p.to_response())
        return ParametroGlobalSuccessResponse(
            message="Consulta de parámetro global exitosa",
            data=data_response,
            success=True
        )