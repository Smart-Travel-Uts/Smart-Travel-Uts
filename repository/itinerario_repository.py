# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# ─────────────────────────────────────────────────────────────

from datetime import date, datetime, timezone
from typing import Optional
from domain.itinerario import ActividadItinerario, Itinerario


class ItinerarioRepository:

    def __init__(self):
        # Almacén en memoria: lista de objetos Itinerario
        self._datos: list[Itinerario] = []
        self._siguiente_id: int = 8842
        self._siguiente_act: int = 3

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self):
        """Carga datos iniciales de ejemplo."""
        itin_ejemplo = Itinerario(
            id_itinerario="ITIN-2026-8841",
            id_usuario="USR-9921",
            titulo="Vacaciones en Bucaramanga y Santander",
            destino_principal="Bucaramanga, Colombia",
            fecha_inicio=date(2026, 11, 10),
            fecha_fin=date(2026, 11, 15),
            moneda="COP",
            presupuesto_monto=1500000.00,
            estado="BORRADOR",
            fecha_creacion=datetime(2026, 10, 25, 21, 30, 0, tzinfo=timezone.utc),
            actividades=[
                ActividadItinerario(
                    id_actividad="ACT-001",
                    tipo="VUELO",
                    referencia_id="VUE-BOG-BGA-102",
                    titulo="Vuelo Bogotá -> Bucaramanga",
                    hora_inicio=datetime(2026, 11, 10, 8, 0, 0, tzinfo=timezone.utc),
                    hora_fin=datetime(2026, 11, 10, 9, 0, 0, tzinfo=timezone.utc),
                    ubicacion={
                        "nombre": "Aeropuerto Palonegro",
                        "coordenadas": [-73.1844, 7.1265],
                    },
                    costo=180000.00,
                    notas="Llevar pase de abordar impreso o en celular",
                ),
                ActividadItinerario(
                    id_actividad="ACT-002",
                    tipo="PUNTO_INTERES",
                    referencia_id="POI-9912",
                    titulo="Visita al Parque San Pío",
                    hora_inicio=datetime(2026, 11, 10, 16, 0, 0, tzinfo=timezone.utc),
                    hora_fin=datetime(2026, 11, 10, 18, 0, 0, tzinfo=timezone.utc),
                    ubicacion={
                        "nombre": "Parque San Pío, Cabecera",
                        "coordenadas": [-73.1112, 7.1189],
                    },
                    costo=0.00,
                    notas="Tomar café en los alrededores",
                ),
            ],
        )
        self._datos = [itin_ejemplo]
        self._siguiente_id = 8842
        self._siguiente_act = 3

    # ── CRUD básico ───────────────────────────────────────────

    def obtener_todos(self) -> list[Itinerario]:
        return self._datos.copy()

    def obtener_por_id(self, id_itinerario: str) -> Optional[Itinerario]:
        buscado = id_itinerario.strip().upper()
        return next((i for i in self._datos if i.id_itinerario == buscado), None)

    def crear(
        self,
        id_usuario: str,
        titulo: str,
        destino_principal: str,
        fecha_inicio: date,
        fecha_fin: date,
        moneda: str = "COP",
        presupuesto_monto: float = 0.0,
    ) -> Itinerario:
        nuevo = Itinerario(
            id_itinerario=f"ITIN-2026-{self._siguiente_id}",
            id_usuario=id_usuario,
            titulo=titulo,
            destino_principal=destino_principal,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            moneda=moneda,
            presupuesto_monto=presupuesto_monto,
            estado="BORRADOR",
            fecha_creacion=datetime.now(timezone.utc),
            actividades=[],
        )
        self._datos.append(nuevo)
        self._siguiente_id += 1
        return nuevo

    def actualizar(
        self,
        id_itinerario: str,
        titulo: str,
        destino_principal: str,
        fecha_inicio: date,
        fecha_fin: date,
        moneda: str,
        presupuesto_monto: float,
    ) -> Optional[Itinerario]:
        itin = self.obtener_por_id(id_itinerario)
        if not itin:
            return None
        itin.titulo = titulo.strip()
        itin.destino_principal = destino_principal.strip()
        itin.fecha_inicio = fecha_inicio
        itin.fecha_fin = fecha_fin
        itin.moneda = moneda.strip().upper()
        itin.presupuesto_monto = round(float(presupuesto_monto), 2)
        return itin

    def eliminar(self, id_itinerario: str) -> bool:
        itin = self.obtener_por_id(id_itinerario)
        if not itin:
            return False
        self._datos.remove(itin)
        return True

    def obtener_por_usuario(self, id_usuario: str) -> list[Itinerario]:
        usuario_limpio = id_usuario.strip().upper()
        return [i for i in self._datos if i.id_usuario == usuario_limpio]

    def generar_id_actividad(self) -> str:
        codigo = f"ACT-{self._siguiente_act:03d}"
        self._siguiente_act += 1
        return codigo

    def eliminar_actividad(self, id_itinerario: str, id_actividad: str) -> bool:
        itin = self.obtener_por_id(id_itinerario)
        if not itin:
            return False
        act_buscada = id_actividad.strip().upper()
        for idx, act in enumerate(itin.actividades):
            if act.id_actividad == act_buscada:
                itin.actividades.pop(idx)
                return True
        return False


# Instancia única compartida (Singleton simple)
itinerario_repository = ItinerarioRepository()