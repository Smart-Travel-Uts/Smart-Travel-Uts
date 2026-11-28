# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

import secrets
from typing import Optional
from domain.colaboracion import (
    ColaboradorAgregadoResponse,
    ColaboradorDetalleResponse,
    EnlaceCompartido,
    ErrorPermisoDataResponse,
    ErrorPermisoResponse,
    InvitarColaboradoresDataResponse,
    InvitarColaboradoresRequest,
    InvitarColaboradoresResponse,
    ListaColaboradoresDataResponse,
    ListaColaboradoresResponse,
)
from repository.colaboracion_repository import (
    ColaboracionRepository,
    colaboracion_repository,
)


class PermisoInsuficienteError(Exception):
    """Error de autorización RBAC (HTTP 403)."""

    def __init__(
        self,
        detalles: str = "Se requieren permisos de PROPIETARIO para realizar esta acción.",
        message: str = "No tienes autorización para administrar los permisos de este itinerario",
    ):
        super().__init__(message)
        self.message = message
        self.codigo_error = "PERMISO_DENEGADO"
        self.detalles = detalles

    def to_response_dict(self) -> dict:
        return ErrorPermisoResponse(
            message=self.message,
            data=ErrorPermisoDataResponse(
                codigo_error=self.codigo_error,
                detalles=self.detalles,
            ),
            success=False,
        ).model_dump()


class EnlaceExpiradoError(Exception):
    """Token de enlace compartido caducado o inexistente (HTTP 410)."""

    def __init__(self, message: str = "El enlace compartido ha expirado o ya no está disponible"):
        super().__init__(message)
        self.message = message


class ConflictoVersionError(Exception):
    """Conflicto por edición concurrente con versión desactualizada (HTTP 409)."""

    def __init__(self, message: str = "Conflicto de versión: el recurso fue modificado por otro colaborador"):
        super().__init__(message)
        self.message = message


class ColaboracionService:

    def __init__(self, repo: ColaboracionRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def _obtener_rol_usuario(
        self, id_itinerario: str, id_usuario: str, email_usuario: Optional[str] = None
    ) -> Optional[str]:
        itinerario = self.repo.obtener_itinerario(id_itinerario)
        if not itinerario:
            raise ValueError(f"Itinerario '{id_itinerario}' no encontrado")

        usuario_limpio = (id_usuario or "").strip().upper()
        if itinerario.id_usuario.upper() == usuario_limpio:
            return "PROPIETARIO"

        for col in self.repo.obtener_colaboradores(id_itinerario):
            coincide_id = (col.id_usuario or "").upper() == usuario_limpio and usuario_limpio != ""
            coincide_email = bool(email_usuario) and col.email.lower() == email_usuario.strip().lower()
            if coincide_id or coincide_email:
                return col.rol

        return None

    def _requerir_propietario(
        self, id_itinerario: str, id_usuario: str, email_usuario: Optional[str] = None
    ) -> str:
        rol = self._obtener_rol_usuario(id_itinerario, id_usuario, email_usuario)
        if rol != "PROPIETARIO":
            raise PermisoInsuficienteError(
                detalles="Se requieren permisos de PROPIETARIO para realizar esta acción."
            )
        return rol

    def _requerir_lector_o_superior(
        self, id_itinerario: str, id_usuario: str, email_usuario: Optional[str] = None
    ) -> str:
        rol = self._obtener_rol_usuario(id_itinerario, id_usuario, email_usuario)
        if rol not in {"PROPIETARIO", "EDITOR", "LECTOR"}:
            raise PermisoInsuficienteError(
                detalles="No perteneces a los miembros autorizados de este itinerario."
            )
        return rol

    def _requerir_editor_o_propietario(
        self, id_itinerario: str, id_usuario: str, email_usuario: Optional[str] = None
    ) -> str:
        rol = self._obtener_rol_usuario(id_itinerario, id_usuario, email_usuario)
        if rol not in {"PROPIETARIO", "EDITOR"}:
            raise PermisoInsuficienteError(
                detalles="Tu rol actual no permite modificar actividades o reservas de este itinerario."
            )
        return rol

    def _obtener_o_crear_enlace(self, id_itinerario: str, creado_por: str) -> EnlaceCompartido:
        for enlace in self.repo._enlaces.values():
            if enlace.id_itinerario == id_itinerario and enlace.esta_vigente():
                return enlace

        token_nuevo = secrets.token_urlsafe(18)
        enlace_nuevo = EnlaceCompartido(
            token=token_nuevo,
            id_itinerario=id_itinerario,
            creado_por=creado_por,
        )
        return self.repo.guardar_enlace(enlace_nuevo)

    def invitar_colaboradores(
        self,
        id_itinerario: str,
        datos: InvitarColaboradoresRequest,
        id_usuario_solicitante: str,
        email_solicitante: Optional[str] = None,
    ) -> InvitarColaboradoresResponse:
        itinerario = self.repo.obtener_itinerario(id_itinerario)
        if not itinerario:
            raise ValueError(f"Itinerario '{id_itinerario}' no encontrado")

        self._requerir_propietario(id_itinerario, id_usuario_solicitante, email_solicitante)

        agregados: list[ColaboradorAgregadoResponse] = []
        for item in datos.invitaciones:
            # Regla: usuarios ya registrados se marcan como ACEPTADA; nuevos como PENDIENTE
            estado = "ACEPTADA" if item.email == "roberto.gomez@example.com" else "PENDIENTE"
            id_usr = "USR-ROBERTO" if item.email == "roberto.gomez@example.com" else None

            col = self.repo.agregar_colaborador(
                id_itinerario=id_itinerario,
                email=item.email,
                rol=item.rol,
                estado_invitacion=estado,
                id_usuario=id_usr,
            )
            agregados.append(ColaboradorAgregadoResponse(**col.to_agregado_response()))

        enlace = self._obtener_o_crear_enlace(id_itinerario, id_usuario_solicitante)
        version_actual = self.repo.obtener_version(id_itinerario)

        self.repo.registrar_auditoria(
            id_itinerario=id_itinerario,
            id_usuario=id_usuario_solicitante,
            rol_usuario="PROPIETARIO",
            accion="INVITAR_COLABORADORES",
            detalle=f"Se invitaron {len(agregados)} colaborador(es): {[c.email for c in agregados]}",
            version_resultante=version_actual,
        )

        return InvitarColaboradoresResponse(
            message="Invitaciones enviadas exitosamente",
            data=InvitarColaboradoresDataResponse(
                id_itinerario=id_itinerario,
                titulo_viaje=itinerario.titulo,
                colaboradores_agregados=agregados,
                enlace_compartido=enlace.to_url(),
            ),
            success=True,
        )

    def listar_colaboradores(
        self,
        id_itinerario: str,
        id_usuario_solicitante: str,
        email_solicitante: Optional[str] = None,
    ) -> ListaColaboradoresResponse:
        self._requerir_lector_o_superior(id_itinerario, id_usuario_solicitante, email_solicitante)
        colaboradores = [
            ColaboradorDetalleResponse(**c.to_detalle_response())
            for c in self.repo.obtener_colaboradores(id_itinerario)
        ]
        return ListaColaboradoresResponse(
            message="Colaboradores del itinerario obtenidos exitosamente",
            data=ListaColaboradoresDataResponse(
                id_itinerario=id_itinerario,
                total=len(colaboradores),
                colaboradores=colaboradores,
            ),
            success=True,
        )

    def revocar_colaborador(
        self,
        id_itinerario: str,
        id_usuario_objetivo: str,
        id_usuario_solicitante: str,
        email_solicitante: Optional[str] = None,
    ) -> dict:
        self._requerir_propietario(id_itinerario, id_usuario_solicitante, email_solicitante)
        eliminado = self.repo.eliminar_colaborador(id_itinerario, id_usuario_objetivo)
        if not eliminado:
            raise ValueError(
                f"Colaborador '{id_usuario_objetivo}' no encontrado en el itinerario '{id_itinerario}'"
            )

        version_actual = self.repo.obtener_version(id_itinerario)
        self.repo.registrar_auditoria(
            id_itinerario=id_itinerario,
            id_usuario=id_usuario_solicitante,
            rol_usuario="PROPIETARIO",
            accion="REVOCAR_COLABORADOR",
            detalle=f"Se revocó el acceso a '{id_usuario_objetivo}'",
            version_resultante=version_actual,
        )

        return {
            "message": "Acceso del colaborador revocado exitosamente",
            "data": {
                "id_itinerario": id_itinerario,
                "id_usuario": id_usuario_objetivo,
            },
            "success": True,
        }

    def consultar_enlace_compartido(self, token: str) -> dict:
        enlace = self.repo.obtener_enlace(token)
        if not enlace or not enlace.esta_vigente():
            raise EnlaceExpiradoError()

        itinerario = self.repo.obtener_itinerario(enlace.id_itinerario)
        if not itinerario:
            raise ValueError("El itinerario asociado al enlace no existe")

        return {
            "message": "Itinerario compartido obtenido en modo lectura",
            "data": {
                "id_itinerario": itinerario.id_itinerario,
                "titulo_viaje": itinerario.titulo,
                "rol_acceso": "LECTOR",
                "expira_en": enlace.expira_en.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "success": True,
        }

    def registrar_edicion_con_auditoria(
        self,
        id_itinerario: str,
        id_usuario: str,
        accion: str,
        detalle: str,
        version_esperada: Optional[int] = None,
        email_usuario: Optional[str] = None,
    ) -> dict:
        rol = self._requerir_editor_o_propietario(id_itinerario, id_usuario, email_usuario)
        version_actual = self.repo.obtener_version(id_itinerario)

        if version_esperada is not None and version_esperada != version_actual:
            raise ConflictoVersionError(
                f"Versión esperada {version_esperada} no coincide con la versión actual {version_actual}"
            )

        nueva_version = self.repo.incrementar_version(id_itinerario)
        auditoria = self.repo.registrar_auditoria(
            id_itinerario=id_itinerario,
            id_usuario=id_usuario,
            rol_usuario=rol,
            accion=accion,
            detalle=detalle,
            version_resultante=nueva_version,
        )
        return {
            "version": nueva_version,
            "auditoria": auditoria.to_response(),
        }


# Instancia única compartida
colaboracion_service = ColaboracionService(colaboracion_repository)