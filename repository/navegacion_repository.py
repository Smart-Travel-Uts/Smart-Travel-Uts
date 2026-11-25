# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from domain.navegacion import PuntoInteres, ServicioCartografiaError


class NavegacionRepository:

    def __init__(self):
        # Almacén en memoria: lista de objetos PuntoInteres
        self._datos: list[PuntoInteres] = []
        self._siguiente_id: int = 9015
        self._simular_fallo: bool = False

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self):
        """Carga puntos de interés iniciales de ejemplo."""
        iniciales = [
            PuntoInteres(
                id_poi="POI-8821",
                nombre="Parque San Pío",
                categoria="PARQUE_CULTURAL",
                latitud=7.1158,
                longitud=-73.1112,
                calificacion_promedio=4.7,
                direccion="Carrera 33 # 45-01",
                horario_apertura="06:00",
                horario_cierre="22:00",
                estado_operativo="ABIERTO",
                activo=True,
            ),
            PuntoInteres(
                id_poi="POI-9014",
                nombre="Restaurante El Santandereano",
                categoria="GASTRONOMIA",
                latitud=7.1210,
                longitud=-73.1201,
                calificacion_promedio=4.5,
                direccion="Calle 36 # 21-14",
                horario_apertura="11:30",
                horario_cierre="21:30",
                estado_operativo="ABIERTO",
                activo=True,
            ),
            PuntoInteres(
                id_poi="POI-9015",
                nombre="Casa de la Cultura Custodio García Rovira",
                categoria="CULTURA",
                latitud=7.1185,
                longitud=-73.1245,
                calificacion_promedio=4.6,
                direccion="Calle 35 # 12-40",
                horario_apertura="08:00",
                horario_cierre="18:00",
                estado_operativo="ABIERTO",
                activo=True,
            ),
            PuntoInteres(
                id_poi="POI-9016",
                nombre="Estación Metrolínea Provenza",
                categoria="TRANSPORTE",
                latitud=7.0860,
                longitud=-73.1190,
                calificacion_promedio=4.1,
                direccion="Autopista Floridablanca # 105-20",
                horario_apertura="05:00",
                horario_cierre="23:00",
                estado_operativo="ABIERTO",
                activo=True,
            ),
            PuntoInteres(
                id_poi="POI-9017",
                nombre="Mirador Histórico Inactivo",
                categoria="HISTORIA",
                latitud=7.1195,
                longitud=-73.1225,
                calificacion_promedio=4.0,
                direccion="Calle 34 # 19-05",
                horario_apertura="09:00",
                horario_cierre="17:00",
                estado_operativo="CERRADO",
                activo=False,
            ),
        ]
        self._datos = iniciales
        self._siguiente_id = 9018

    # ── Control de disponibilidad / fallo geoespacial (503) ──

    def configurar_fallo(self, simular_fallo: bool) -> None:
        """Simula caída, timeout o sobrecarga de la base de datos espacial / PostGIS."""
        self._simular_fallo = simular_fallo

    # ── CRUD básico ───────────────────────────────────────────

    def obtener_todos(self) -> list[PuntoInteres]:
        if self._simular_fallo:
            raise ServicioCartografiaError(
                "Servicio de cartografía no disponible temporalmente"
            )
        return self._datos.copy()

    def obtener_por_id(self, id_poi: str) -> Optional[PuntoInteres]:
        if self._simular_fallo:
            raise ServicioCartografiaError(
                "Servicio de cartografía no disponible temporalmente"
            )
        buscado = id_poi.strip().upper()
        return next((p for p in self._datos if p.id_poi == buscado), None)

    def crear(
        self,
        nombre: str,
        categoria: str,
        latitud: float,
        longitud: float,
        calificacion_promedio: float,
        direccion: str,
        horario_apertura: str,
        horario_cierre: str,
        estado_operativo: str = "ABIERTO",
        activo: bool = True,
    ) -> PuntoInteres:
        if self._simular_fallo:
            raise ServicioCartografiaError(
                "Servicio de cartografía no disponible temporalmente"
            )
        nuevo = PuntoInteres(
            id_poi=f"POI-{self._siguiente_id}",
            nombre=nombre,
            categoria=categoria,
            latitud=latitud,
            longitud=longitud,
            calificacion_promedio=calificacion_promedio,
            direccion=direccion,
            horario_apertura=horario_apertura,
            horario_cierre=horario_cierre,
            estado_operativo=estado_operativo,
            activo=activo,
        )
        self._datos.append(nuevo)
        self._siguiente_id += 1
        return nuevo

    def actualizar(
        self,
        id_poi: str,
        nombre: str,
        categoria: str,
        latitud: float,
        longitud: float,
        calificacion_promedio: float,
        direccion: str,
        horario_apertura: str,
        horario_cierre: str,
        estado_operativo: str,
        activo: bool,
    ) -> Optional[PuntoInteres]:
        poi = self.obtener_por_id(id_poi)
        if not poi:
            return None
        poi.nombre = nombre
        poi.categoria = categoria.strip().upper()
        poi.latitud = float(latitud)
        poi.longitud = float(longitud)
        poi.calificacion_promedio = round(float(calificacion_promedio), 2)
        poi.direccion = direccion
        poi.horario_apertura = horario_apertura
        poi.horario_cierre = horario_cierre
        poi.estado_operativo = estado_operativo.strip().upper()
        poi.activo = bool(activo)
        return poi

    def eliminar(self, id_poi: str) -> bool:
        poi = self.obtener_por_id(id_poi)
        if not poi:
            return False
        self._datos.remove(poi)
        return True

    def obtener_por_categoria(self, categoria: str) -> list[PuntoInteres]:
        if self._simular_fallo:
            raise ServicioCartografiaError(
                "Servicio de cartografía no disponible temporalmente"
            )
        cat = categoria.strip().upper()
        return [p for p in self._datos if p.categoria == cat]


# Instancia única compartida (Singleton simple)
navegacion_repository = NavegacionRepository()