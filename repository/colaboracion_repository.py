# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# ─────────────────────────────────────────────────────────────

from datetime import datetime, timedelta, timezone
from typing import Optional
from domain.colaboracion import (
    ColaboradorItinerario,
    EnlaceCompartido,
    RegistroAuditoria,
)
from domain.itinerario import Itinerario
from repository.itinerario_repository import (
    ItinerarioRepository,
    itinerario_repository,
)


class ColaboracionRepository:

    def __init__(self, itin_repo: ItinerarioRepository):
        # Conexión con el repositorio de itinerarios (HU-13)
        self.itin_repo = itin_repo
        # Diccionario por id_itinerario -> lista de ColaboradorItinerario
        self._colaboradores: dict[str, list[ColaboradorItinerario]] = {}
        # Diccionario por token -> EnlaceCompartido
        self._enlaces: dict[str, EnlaceCompartido] = {}
        # Diccionario por id_itinerario -> lista de RegistroAuditoria
        self._auditorias: dict[str, list[RegistroAuditoria]] = {}
        # Diccionario por id_itinerario -> versión actual para bloqueo optimista
        self._versiones: dict[str, int] = {}
        self._siguiente_col: int = 1
        self._siguiente_aud: int = 1

        # Datos de ejemplo para arrancar el sistema
        self._seed()

    def _seed(self):
        """Carga datos iniciales de ejemplo para pruebas y operación."""
        ahora = datetime.now(timezone.utc)

        # Asegurar itinerario de ejemplo ITIN-2026-8841 si aún no existe en HU-13
        if self.itin_repo.obtener_por_id("ITIN-2026-8841") is None:
            itin_demo = Itinerario(
                id_itinerario="ITIN-2026-8841",
                id_usuario="USR-9921",
                titulo="Ruta por el Caribe Colombiano",
                fecha_inicio=ahora + timedelta(days=10),
                fecha_fin=ahora + timedelta(days=15),
                descripcion="Itinerario colaborativo de prueba",
            )
            self.itin_repo._itinerarios["ITIN-2026-8841"] = itin_demo

        self._versiones["ITIN-2026-8841"] = 1

        # Colaboradores iniciales (incluye LECTOR para Caso 2)
        self._colaboradores["ITIN-2026-8841"] = [
            ColaboradorItinerario(
                id_colaborador="COL-000",
                email="propietario@smarttravel.app",
                rol="PROPIETARIO",
                estado_invitacion="ACEPTADA",
                id_usuario="USR-9921",
                fecha_invitacion=ahora,
            ),
            ColaboradorItinerario(
                id_colaborador="COL-002",
                email="roberto.gomez@example.com",
                rol="LECTOR",
                estado_invitacion="ACEPTADA",
                id_usuario="USR-ROBERTO",
                fecha_invitacion=ahora,
            ),
        ]

        # Enlace expirado de ejemplo para Caso 5
        self._enlaces["TOKEN_EXPIRADO"] = EnlaceCompartido(
            token="TOKEN_EXPIRADO",
            id_itinerario="ITIN-2026-8841",
            creado_por="USR-9921",
            expira_en=ahora - timedelta(hours=2),
            activo=True,
        )

        self._auditorias["ITIN-2026-8841"] = [
            RegistroAuditoria(
                id_auditoria="AUD-001",
                id_itinerario="ITIN-2026-8841",
                id_usuario="USR-9921",
                rol_usuario="PROPIETARIO",
                accion="CREAR_ITINERARIO",
                detalle="Itinerario inicial creado",
                version_resultante=1,
                fecha_hora_utc=ahora,
            )
        ]
        self._siguiente_col = 3
        self._siguiente_aud = 2

    # ── Consulta y persistencia de colaboradores ──────────────

    def obtener_itinerario(self, id_itinerario: str) -> Optional[Itinerario]:
        return self.itin_repo.obtener_por_id(id_itinerario)

    def obtener_colaboradores(self, id_itinerario: str) -> list[ColaboradorItinerario]:
        return list(self._colaboradores.get(id_itinerario, []))

    def agregar_colaborador(
        self,
        id_itinerario: str,
        email: str,
        rol: str,
        estado_invitacion: str = "PENDIENTE",
        id_usuario: Optional[str] = None,
    ) -> ColaboradorItinerario:
        lista = self._colaboradores.setdefault(id_itinerario, [])
        existente = next(
            (c for c in lista if c.email.lower() == email.strip().lower()),
            None,
        )
        if existente:
            existente.rol = rol.strip().upper()
            existente.estado_invitacion = estado_invitacion.strip().upper()
            if id_usuario:
                existente.id_usuario = id_usuario.strip().upper()
            return existente

        nuevo = ColaboradorItinerario(
            id_colaborador=f"COL-{self._siguiente_col:03d}",
            email=email,
            rol=rol,
            estado_invitacion=estado_invitacion,
            id_usuario=id_usuario,
        )
        self._siguiente_col += 1
        lista.append(nuevo)
        return nuevo

    def eliminar_colaborador(self, id_itinerario: str, id_usuario_o_col: str) -> bool:
        lista = self._colaboradores.get(id_itinerario, [])
        objetivo = id_usuario_o_col.strip().upper()
        for idx, col in enumerate(lista):
            if col.rol == "PROPIETARIO":
                continue
            coincide_id = (col.id_usuario or "").upper() == objetivo
            coincide_col = col.id_colaborador.upper() == objetivo
            coincide_email = col.email.upper() == objetivo
            if coincide_id or coincide_col or coincide_email:
                lista.pop(idx)
                return True
        return False

    # ── Enlaces compartidos y auditoría ───────────────────────

    def guardar_enlace(self, enlace: EnlaceCompartido) -> EnlaceCompartido:
        self._enlaces[enlace.token] = enlace
        return enlace

    def obtener_enlace(self, token: str) -> Optional[EnlaceCompartido]:
        return self._enlaces.get(token.strip())

    def obtener_version(self, id_itinerario: str) -> int:
        return self._versiones.get(id_itinerario, 1)

    def incrementar_version(self, id_itinerario: str) -> int:
        nueva = self.obtener_version(id_itinerario) + 1
        self._versiones[id_itinerario] = nueva
        return nueva

    def registrar_auditoria(
        self,
        id_itinerario: str,
        id_usuario: str,
        rol_usuario: str,
        accion: str,
        detalle: str,
        version_resultante: int,
    ) -> RegistroAuditoria:
        registro = RegistroAuditoria(
            id_auditoria=f"AUD-{self._siguiente_aud:03d}",
            id_itinerario=id_itinerario,
            id_usuario=id_usuario,
            rol_usuario=rol_usuario,
            accion=accion,
            detalle=detalle,
            version_resultante=version_resultante,
        )
        self._siguiente_aud += 1
        self._auditorias.setdefault(id_itinerario, []).append(registro)
        return registro

    def obtener_auditorias(self, id_itinerario: str) -> list[RegistroAuditoria]:
        return list(self._auditorias.get(id_itinerario, []))


# Instancia única compartida (Singleton simple)
colaboracion_repository = ColaboracionRepository(itinerario_repository)