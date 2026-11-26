# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# ─────────────────────────────────────────────────────────────

from datetime import datetime, timezone
from typing import Optional
from domain.clima import AlertaLocal, PronosticoDestino


class ClimaRepository:

    def __init__(self):
        # Destinos preconfigurados por id_destino -> metadatos de ubicación
        self._destinos: dict[str, dict] = {}
        # Pronósticos base en memoria por clave normalizada de ubicación
        self._pronosticos: dict[str, PronosticoDestino] = {}
        # Caché en memoria por clave: {"pronostico": PronosticoDestino, "guardado_en": datetime}
        self._cache: dict[str, dict] = {}
        # Bandera para simular caída del proveedor externo en pruebas (Caso 5)
        self.simular_fallo_proveedor: bool = False

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self):
        """Carga destinos y pronósticos iniciales de ejemplo."""
        self._destinos = {
            "DEST-BGA": {
                "id_destino": "DEST-BGA",
                "nombre": "Bucaramanga, Santander",
                "latitud": 7.1193,
                "longitud": -73.1227,
            },
            "DEST-CTG": {
                "id_destino": "DEST-CTG",
                "nombre": "Cartagena de Indias, Bolívar",
                "latitud": 10.3910,
                "longitud": -75.4794,
            },
            "DEST-MED": {
                "id_destino": "DEST-MED",
                "nombre": "Medellín, Antioquia",
                "latitud": 6.2442,
                "longitud": -75.5812,
            },
        }

        alerta_bga = AlertaLocal(
            id_alerta="ALT-2026-091",
            tipo="METEOROLOGICA",
            nivel_riesgo="ADVERTENCIA",
            titulo="Alerta Amarilla por Lluvias e Incremental de Caudal",
            descripcion="Se prevén precipitaciones intensas en la zona metropolitana durante las próximas 6 horas.",
            emitido_por="IDEAM / Gestión del Riesgo",
            fecha_emision="2026-10-25T18:00:00Z",
            fecha_expiracion="2026-10-26T06:00:00Z",
        )

        pronostico_bga = PronosticoDestino(
            nombre_destino="Bucaramanga, Santander",
            latitud=7.1193,
            longitud=-73.1227,
            clima_actual={
                "fecha_hora_utc": "2026-10-25T21:30:00Z",
                "temperatura_celsius": 24.5,
                "sensacion_termica_celsius": 25.8,
                "condicion": "LLUVIA_MODERADA",
                "descripcion": "Lluvias moderadas intermitentes",
                "humedad_porcentaje": 82,
                "velocidad_viento_kmh": 12.4,
                "indice_uv": 3,
            },
            alertas_activas=[alerta_bga],
            pronostico_dias=[
                {
                    "fecha": "2026-10-26",
                    "temperatura_max_celsius": 27.0,
                    "temperatura_min_celsius": 18.5,
                    "probabilidad_precipitacion_porcentaje": 75,
                    "condicion_principal": "CHUBASCOS",
                },
                {
                    "fecha": "2026-10-27",
                    "temperatura_max_celsius": 29.1,
                    "temperatura_min_celsius": 19.0,
                    "probabilidad_precipitacion_porcentaje": 20,
                    "condicion_principal": "PARCIALMENTE_NUBLADO",
                },
                {
                    "fecha": "2026-10-28",
                    "temperatura_max_celsius": 28.4,
                    "temperatura_min_celsius": 18.8,
                    "probabilidad_precipitacion_porcentaje": 35,
                    "condicion_principal": "PARCIALMENTE_NUBLADO",
                },
                {
                    "fecha": "2026-10-29",
                    "temperatura_max_celsius": 26.5,
                    "temperatura_min_celsius": 18.2,
                    "probabilidad_precipitacion_porcentaje": 65,
                    "condicion_principal": "LLUVIA_MODERADA",
                },
                {
                    "fecha": "2026-10-30",
                    "temperatura_max_celsius": 27.8,
                    "temperatura_min_celsius": 18.6,
                    "probabilidad_precipitacion_porcentaje": 40,
                    "condicion_principal": "DESPEJADO",
                },
                {
                    "fecha": "2026-10-31",
                    "temperatura_max_celsius": 28.9,
                    "temperatura_min_celsius": 19.1,
                    "probabilidad_precipitacion_porcentaje": 25,
                    "condicion_principal": "PARCIALMENTE_NUBLADO",
                },
                {
                    "fecha": "2026-11-01",
                    "temperatura_max_celsius": 27.3,
                    "temperatura_min_celsius": 18.4,
                    "probabilidad_precipitacion_porcentaje": 50,
                    "condicion_principal": "CHUBASCOS",
                },
            ],
        )

        self._pronosticos["7.1193:-73.1227"] = pronostico_bga

    # ── Consulta de destinos y pronósticos ────────────────────

    def obtener_destino_por_id(self, id_destino: str) -> Optional[dict]:
        return self._destinos.get(id_destino.strip().upper())

    def obtener_pronostico_proveedor(
        self, nombre_destino: str, latitud: float, longitud: float
    ) -> PronosticoDestino:
        clave = f"{round(float(latitud), 4)}:{round(float(longitud), 4)}"
        existente = self._pronosticos.get(clave)
        if existente:
            return existente

        # Pronóstico base por defecto para cualquier coordenada válida no precargada
        nuevo = PronosticoDestino(
            nombre_destino=nombre_destino,
            latitud=latitud,
            longitud=longitud,
            clima_actual={
                "fecha_hora_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "temperatura_celsius": 25.0,
                "sensacion_termica_celsius": 26.0,
                "condicion": "PARCIALMENTE_NUBLADO",
                "descripcion": "Cielo parcialmente nublado con brisa leve",
                "humedad_porcentaje": 70,
                "velocidad_viento_kmh": 10.5,
                "indice_uv": 5,
            },
            alertas_activas=[],
            pronostico_dias=[
                {
                    "fecha": "2026-10-26",
                    "temperatura_max_celsius": 28.0,
                    "temperatura_min_celsius": 19.0,
                    "probabilidad_precipitacion_porcentaje": 25,
                    "condicion_principal": "PARCIALMENTE_NUBLADO",
                },
                {
                    "fecha": "2026-10-27",
                    "temperatura_max_celsius": 29.0,
                    "temperatura_min_celsius": 19.5,
                    "probabilidad_precipitacion_porcentaje": 15,
                    "condicion_principal": "DESPEJADO",
                },
                {
                    "fecha": "2026-10-28",
                    "temperatura_max_celsius": 27.5,
                    "temperatura_min_celsius": 18.8,
                    "probabilidad_precipitacion_porcentaje": 45,
                    "condicion_principal": "CHUBASCOS",
                },
                {
                    "fecha": "2026-10-29",
                    "temperatura_max_celsius": 28.2,
                    "temperatura_min_celsius": 19.2,
                    "probabilidad_precipitacion_porcentaje": 30,
                    "condicion_principal": "PARCIALMENTE_NUBLADO",
                },
                {
                    "fecha": "2026-10-30",
                    "temperatura_max_celsius": 29.5,
                    "temperatura_min_celsius": 20.0,
                    "probabilidad_precipitacion_porcentaje": 10,
                    "condicion_principal": "DESPEJADO",
                },
                {
                    "fecha": "2026-10-31",
                    "temperatura_max_celsius": 27.8,
                    "temperatura_min_celsius": 18.7,
                    "probabilidad_precipitacion_porcentaje": 35,
                    "condicion_principal": "PARCIALMENTE_NUBLADO",
                },
                {
                    "fecha": "2026-11-01",
                    "temperatura_max_celsius": 26.9,
                    "temperatura_min_celsius": 18.3,
                    "probabilidad_precipitacion_porcentaje": 55,
                    "condicion_principal": "LLUVIA_MODERADA",
                },
            ],
        )
        self._pronosticos[clave] = nuevo
        return nuevo

    # ── Operaciones de caché en memoria ───────────────────────

    def obtener_cache(self, clave: str) -> Optional[dict]:
        return self._cache.get(clave)

    def guardar_cache(
        self, clave: str, pronostico: PronosticoDestino, guardado_en: datetime
    ) -> None:
        self._cache[clave] = {
            "pronostico": pronostico,
            "guardado_en": guardado_en,
        }

    def limpiar_cache(self) -> None:
        self._cache.clear()


# Instancia única compartida (Singleton simple)
clima_repository = ClimaRepository()