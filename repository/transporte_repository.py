# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from domain.transporte import RutaUrbana, ServicioRuteoError


class TransporteRepository:

    def __init__(self):
        # Almacén en memoria: lista de objetos RutaUrbana
        self._datos: list[RutaUrbana] = []
        self._siguiente_id: int = 103
        self._simular_fallo: bool = False

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self):
        """Carga rutas urbanas y paradas iniciales de ejemplo."""
        iniciales = [
            RutaUrbana(
                id_ruta="RUT-TR-102",
                nombre_linea="Línea T3 - Metrobus",
                tipo_transporte="AUTOBUS_RAPIDO",
                lat_inicio=7.1193,
                lon_inicio=-73.1227,
                lat_fin=7.1381,
                lon_fin=-73.1182,
                duracion_estimada_minutos=18,
                distancia_total_km=3.4,
                tarifa_monto=3000.00,
                frecuencia_minutos=10,
                paradas_plantilla=[
                    {
                        "nombre_parada": "Estación Parque Turbay",
                        "longitud": -73.1215,
                        "latitud": 7.1230,
                        "offset_minutos": 4,
                    },
                    {
                        "nombre_parada": "Estación Quebradaseca",
                        "longitud": -73.1200,
                        "latitud": 7.1290,
                        "offset_minutos": 10,
                    },
                    {
                        "nombre_parada": "Estación Portal Real",
                        "longitud": -73.1182,
                        "latitud": 7.1381,
                        "offset_minutos": 18,
                    },
                ],
                estado_servicio="NORMAL",
                moneda="COP",
                activa=True,
            ),
            RutaUrbana(
                id_ruta="RUT-URB-05",
                nombre_linea="Ruta 15 - San Martin",
                tipo_transporte="AUTOBUS_CONVENCIONAL",
                lat_inicio=7.1193,
                lon_inicio=-73.1227,
                lat_fin=7.1381,
                lon_fin=-73.1182,
                duracion_estimada_minutos=25,
                distancia_total_km=4.1,
                tarifa_monto=2800.00,
                frecuencia_minutos=15,
                paradas_plantilla=[],
                estado_servicio="RETRASADO_LEVE",
                moneda="COP",
                activa=True,
            ),
            RutaUrbana(
                id_ruta="RUT-MET-01",
                nombre_linea="Línea Central Urbana",
                tipo_transporte="METRO",
                lat_inicio=7.1193,
                lon_inicio=-73.1227,
                lat_fin=7.1381,
                lon_fin=-73.1182,
                duracion_estimada_minutos=14,
                distancia_total_km=3.2,
                tarifa_monto=3100.00,
                frecuencia_minutos=8,
                paradas_plantilla=[
                    {
                        "nombre_parada": "Estación Centro",
                        "longitud": -73.1205,
                        "latitud": 7.1275,
                        "offset_minutos": 6,
                    },
                ],
                estado_servicio="NORMAL",
                moneda="COP",
                activa=True,
            ),
            RutaUrbana(
                id_ruta="RUT-TRV-04",
                nombre_linea="Tranvía Cultural Norte",
                tipo_transporte="TRANVIA",
                lat_inicio=7.1193,
                lon_inicio=-73.1227,
                lat_fin=7.1381,
                lon_fin=-73.1182,
                duracion_estimada_minutos=21,
                distancia_total_km=3.7,
                tarifa_monto=2950.00,
                frecuencia_minutos=12,
                paradas_plantilla=[
                    {
                        "nombre_parada": "Parada Parque García Rovira",
                        "longitud": -73.1210,
                        "latitud": 7.1255,
                        "offset_minutos": 7,
                    },
                ],
                estado_servicio="NORMAL",
                moneda="COP",
                activa=True,
            ),
        ]
        self._datos = iniciales
        self._siguiente_id = 103

    # ── Disponibilidad del motor GTFS / BD (503) ─────────────

    def configurar_fallo(self, simular_fallo: bool) -> None:
        """Simula caída, timeout o indisponibilidad del motor de ruteo GTFS / BD."""
        self._simular_fallo = simular_fallo

    # ── CRUD básico ───────────────────────────────────────────

    def obtener_todos(self) -> list[RutaUrbana]:
        if self._simular_fallo:
            raise ServicioRuteoError(
                "Servicio de ruteo de transporte temporalmente no disponible"
            )
        return self._datos.copy()

    def obtener_por_id(self, id_ruta: str) -> Optional[RutaUrbana]:
        if self._simular_fallo:
            raise ServicioRuteoError(
                "Servicio de ruteo de transporte temporalmente no disponible"
            )
        buscado = id_ruta.strip().upper()
        return next((r for r in self._datos if r.id_ruta == buscado), None)

    def crear(
        self,
        nombre_linea: str,
        tipo_transporte: str,
        lat_inicio: float,
        lon_inicio: float,
        lat_fin: float,
        lon_fin: float,
        duracion_estimada_minutos: int,
        distancia_total_km: float,
        tarifa_monto: float,
        frecuencia_minutos: int,
        estado_servicio: str = "NORMAL",
    ) -> RutaUrbana:
        if self._simular_fallo:
            raise ServicioRuteoError(
                "Servicio de ruteo de transporte temporalmente no disponible"
            )
        nueva = RutaUrbana(
            id_ruta=f"RUT-URB-{self._siguiente_id}",
            nombre_linea=nombre_linea,
            tipo_transporte=tipo_transporte,
            lat_inicio=lat_inicio,
            lon_inicio=lon_inicio,
            lat_fin=lat_fin,
            lon_fin=lon_fin,
            duracion_estimada_minutos=duracion_estimada_minutos,
            distancia_total_km=distancia_total_km,
            tarifa_monto=tarifa_monto,
            frecuencia_minutos=frecuencia_minutos,
            paradas_plantilla=[],
            estado_servicio=estado_servicio,
            activa=True,
        )
        self._datos.append(nueva)
        self._siguiente_id += 1
        return nueva

    def actualizar(
        self,
        id_ruta: str,
        nombre_linea: str,
        tipo_transporte: str,
        duracion_estimada_minutos: int,
        distancia_total_km: float,
        tarifa_monto: float,
        frecuencia_minutos: int,
        estado_servicio: str,
    ) -> Optional[RutaUrbana]:
        ruta = self.obtener_por_id(id_ruta)
        if not ruta:
            return None
        ruta.nombre_linea = nombre_linea.strip()
        ruta.tipo_transporte = tipo_transporte.strip().upper()
        ruta.duracion_estimada_minutos = int(duracion_estimada_minutos)
        ruta.distancia_total_km = round(float(distancia_total_km), 1)
        ruta.tarifa_monto = round(float(tarifa_monto), 2)
        ruta.frecuencia_minutos = int(frecuencia_minutos)
        ruta.estado_servicio = estado_servicio.strip().upper()
        return ruta

    def eliminar(self, id_ruta: str) -> bool:
        ruta = self.obtener_por_id(id_ruta)
        if not ruta:
            return False
        self._datos.remove(ruta)
        return True

    def obtener_por_tipo(self, tipo_transporte: str) -> list[RutaUrbana]:
        if self._simular_fallo:
            raise ServicioRuteoError(
                "Servicio de ruteo de transporte temporalmente no disponible"
            )
        limpio = tipo_transporte.strip().upper()
        if limpio == "TODOS":
            return [r for r in self._datos if r.activa]
        return [r for r in self._datos if r.activa and r.tipo_transporte == limpio]


# Instancia única compartida (Singleton simple)
transporte_repository = TransporteRepository()