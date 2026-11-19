from domain.regla_comercial import ReglaComercial, PoliticaCancelacion
from typing import Optional


class ReglaComercialRepository:
    def __init__(self):
        self._reglas: dict[str, ReglaComercial] = {}
        self._seed()

    def _seed(self):
        """Precarga las reglas comerciales vigentes en memoria."""
        datos_iniciales = [
            ReglaComercial(
                tipo_servicio="ALOJAMIENTO",
                porcentaje_comision_freemium=8.0,
                politica_cancelacion=PoliticaCancelacion(
                    tramo_gratuito_horas=72,
                    penalizacion_24h_porcentaje=50.0,
                    penalizacion_mismo_dia_porcentaje=100.0
                ),
                estado="ACTIVO"
            ),
            ReglaComercial(
                tipo_servicio="VUELO",
                porcentaje_comision_freemium=10.0,
                politica_cancelacion=PoliticaCancelacion(
                    tramo_gratuito_horas=48,
                    penalizacion_24h_porcentaje=75.0,
                    penalizacion_mismo_dia_porcentaje=100.0
                ),
                estado="ACTIVO"
            ),
            ReglaComercial(
                tipo_servicio="EVENTO",
                porcentaje_comision_freemium=10.0,
                politica_cancelacion=PoliticaCancelacion(
                    tramo_gratuito_horas=24,
                    penalizacion_24h_porcentaje=50.0,
                    penalizacion_mismo_dia_porcentaje=100.0
                ),
                estado="ACTIVO"
            )
        ]

        for regla in datos_iniciales:
            self._reglas[regla.tipo_servicio] = regla

    def obtener_por_tipo_servicio(self, tipo_servicio: str) -> Optional[ReglaComercial]:
        """Busca una regla comercial por su tipo de servicio."""
        return self._reglas.get(tipo_servicio.upper())


# Instancia Singleton para inyectar en el servicio
regla_comercial_repository = ReglaComercialRepository()