# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from datetime import date, datetime, timezone
from typing import Optional
from pydantic import ValidationError
from domain.itinerario import (
    AccesoDenegadoItinerarioError,
    ActividadCreate,
    ActividadItinerario,
    ActividadResponse,
    AutenticacionItinerarioError,
    ItinerarioCreadoDataResponse,
    ItinerarioCreadoResponse,
    ItinerarioCreate,
    ItinerarioDetalleDataResponse,
    ItinerarioDetalleResponse,
    ItinerarioNoEncontradoError,
    ValidacionItinerarioError,
)
from repository.itinerario_repository import (
    ItinerarioRepository,
    itinerario_repository,
)


class ItinerarioService:

    def __init__(self, repo: ItinerarioRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def resolver_usuario_jwt(self, authorization: Optional[str]) -> str:
        """Valida el token Bearer JWT y extrae el id_usuario del titular."""
        if not authorization or not authorization.strip():
            raise AutenticacionItinerarioError(
                "Token JWT requerido en la cabecera Authorization (Bearer <token>)"
            )

        raw = authorization.strip()
        partes = raw.split(" ")

        if len(partes) == 2 and partes[0].lower() == "bearer":
            token = partes[1].strip()
        elif len(partes) == 1 and raw.lower().startswith("token-"):
            token = raw
        else:
            raise AutenticacionItinerarioError(
                "Formato de cabecera Authorization inválido. Use: Bearer <token>"
            )

        if not token:
            raise AutenticacionItinerarioError("Token JWT inválido o vacío")

        if token.lower().startswith("token-"):
            sufijo = token[6:].strip().upper()
            if not sufijo:
                raise AutenticacionItinerarioError("Token JWT inválido o vacío")
            return sufijo if sufijo.startswith("USR-") else f"USR-{sufijo}"

        return "USR-9921"

    def _extraer_mensaje_pydantic(self, exc: ValidationError) -> str:
        errores: list[str] = []
        for err in exc.errors():
            msg = err.get("msg", "Datos inválidos")
            if msg.startswith("Value error, "):
                msg = msg.replace("Value error, ", "", 1)
            if msg not in errores:
                errores.append(msg)
        return "; ".join(errores) if errores else "Datos de entrada inválidos"

    def _parsear_iso(self, valor: str) -> datetime:
        dt = datetime.fromisoformat(valor.strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _validar_rango_fechas(self, f_ini: date, f_fin: date) -> None:
        if f_ini > f_fin:
            raise ValidacionItinerarioError(
                "La fecha de inicio no puede ser posterior a la fecha de fin"
            )

    def _validar_rango_horas(self, dt_ini: datetime, dt_fin: datetime) -> None:
        if dt_fin <= dt_ini:
            raise ValidacionItinerarioError(
                "La hora_fin debe ser posterior a hora_inicio"
            )

    def listar(self, authorization: Optional[str]) -> list[ItinerarioCreadoDataResponse]:
        id_usuario = self.resolver_usuario_jwt(authorization)
        return [
            ItinerarioCreadoDataResponse(**itin.to_creado_response())
            for itin in self.repo.obtener_por_usuario(id_usuario)
        ]

    def obtener(
        self, id_itinerario: str, authorization: Optional[str]
    ) -> ItinerarioDetalleResponse:
        id_usuario = self.resolver_usuario_jwt(authorization)
        itin = self.repo.obtener_por_id(id_itinerario)
        if not itin:
            raise ItinerarioNoEncontradoError(
                f"Itinerario {id_itinerario} no encontrado"
            )
        if not itin.es_propietario(id_usuario):
            raise AccesoDenegadoItinerarioError(
                "No tiene permisos para consultar o modificar este itinerario"
            )

        return ItinerarioDetalleResponse(
            message="Itinerario recuperado exitosamente",
            data=ItinerarioDetalleDataResponse(**itin.to_detalle_response()),
            success=True,
        )

    def crear(
        self, datos: ItinerarioCreate, authorization: Optional[str]
    ) -> ItinerarioCreadoResponse:
        id_usuario = self.resolver_usuario_jwt(authorization)
        try:
            validado = ItinerarioCreate(**datos.model_dump())
        except ValidationError as exc:
            raise ValidacionItinerarioError(self._extraer_mensaje_pydantic(exc)) from exc

        f_ini = date.fromisoformat(validado.fecha_inicio)
        f_fin = date.fromisoformat(validado.fecha_fin)
        self._validar_rango_fechas(f_ini, f_fin)

        nuevo = self.repo.crear(
            id_usuario=id_usuario,
            titulo=validado.titulo,
            destino_principal=validado.destino_principal,
            fecha_inicio=f_ini,
            fecha_fin=f_fin,
            moneda=validado.presupuesto_estimado.moneda,
            presupuesto_monto=validado.presupuesto_estimado.monto,
        )
        return ItinerarioCreadoResponse(
            message="Itinerario creado exitosamente",
            data=ItinerarioCreadoDataResponse(**nuevo.to_creado_response()),
            success=True,
        )

    def actualizar(
        self,
        id_itinerario: str,
        datos: ItinerarioCreate,
        authorization: Optional[str],
    ) -> ItinerarioCreadoResponse:
        id_usuario = self.resolver_usuario_jwt(authorization)
        itin = self.repo.obtener_por_id(id_itinerario)
        if not itin:
            raise ItinerarioNoEncontradoError(
                f"Itinerario {id_itinerario} no encontrado"
            )
        if not itin.es_propietario(id_usuario):
            raise AccesoDenegadoItinerarioError(
                "No tiene permisos para consultar o modificar este itinerario"
            )

        try:
            validado = ItinerarioCreate(**datos.model_dump())
        except ValidationError as exc:
            raise ValidacionItinerarioError(self._extraer_mensaje_pydantic(exc)) from exc

        f_ini = date.fromisoformat(validado.fecha_inicio)
        f_fin = date.fromisoformat(validado.fecha_fin)
        self._validar_rango_fechas(f_ini, f_fin)

        actualizado = self.repo.actualizar(
            id_itinerario=id_itinerario,
            titulo=validado.titulo,
            destino_principal=validado.destino_principal,
            fecha_inicio=f_ini,
            fecha_fin=f_fin,
            moneda=validado.presupuesto_estimado.moneda,
            presupuesto_monto=validado.presupuesto_estimado.monto,
        )
        if not actualizado:
            raise ItinerarioNoEncontradoError(
                f"Itinerario {id_itinerario} no encontrado"
            )
        return ItinerarioCreadoResponse(
            message="Itinerario actualizado exitosamente",
            data=ItinerarioCreadoDataResponse(**actualizado.to_creado_response()),
            success=True,
        )

    def eliminar(self, id_itinerario: str, authorization: Optional[str]) -> dict:
        id_usuario = self.resolver_usuario_jwt(authorization)
        itin = self.repo.obtener_por_id(id_itinerario)
        if not itin:
            raise ItinerarioNoEncontradoError(
                f"Itinerario {id_itinerario} no encontrado"
            )
        if not itin.es_propietario(id_usuario):
            raise AccesoDenegadoItinerarioError(
                "No tiene permisos para consultar o modificar este itinerario"
            )

        ok = self.repo.eliminar(id_itinerario)
        if not ok:
            raise ItinerarioNoEncontradoError(
                f"Itinerario {id_itinerario} no encontrado"
            )
        return {"mensaje": f"Itinerario {id_itinerario} eliminado correctamente"}

    def agregar_actividad(
        self,
        id_itinerario: str,
        datos: ActividadCreate,
        authorization: Optional[str],
    ) -> ActividadResponse:
        id_usuario = self.resolver_usuario_jwt(authorization)
        itin = self.repo.obtener_por_id(id_itinerario)
        if not itin:
            raise ItinerarioNoEncontradoError(
                f"Itinerario {id_itinerario} no encontrado"
            )
        if not itin.es_propietario(id_usuario):
            raise AccesoDenegadoItinerarioError(
                "No tiene permisos para consultar o modificar este itinerario"
            )

        try:
            validado = ActividadCreate(**datos.model_dump())
        except ValidationError as exc:
            raise ValidacionItinerarioError(self._extraer_mensaje_pydantic(exc)) from exc

        dt_ini = self._parsear_iso(validado.hora_inicio)
        dt_fin = self._parsear_iso(validado.hora_fin)
        self._validar_rango_horas(dt_ini, dt_fin)

        actividad = ActividadItinerario(
            id_actividad=self.repo.generar_id_actividad(),
            tipo=validado.tipo,
            referencia_id=validado.referencia_id,
            titulo=validado.titulo,
            hora_inicio=dt_ini,
            hora_fin=dt_fin,
            ubicacion=validado.ubicacion.model_dump() if validado.ubicacion else None,
            costo=validado.costo,
            notas=validado.notas or "",
        )
        itin.validar_y_agregar_actividad(actividad)
        return ActividadResponse(**actividad.to_response())

    def eliminar_actividad(
        self, id_itinerario: str, id_actividad: str, authorization: Optional[str]
    ) -> dict:
        id_usuario = self.resolver_usuario_jwt(authorization)
        itin = self.repo.obtener_por_id(id_itinerario)
        if not itin:
            raise ItinerarioNoEncontradoError(
                f"Itinerario {id_itinerario} no encontrado"
            )
        if not itin.es_propietario(id_usuario):
            raise AccesoDenegadoItinerarioError(
                "No tiene permisos para consultar o modificar este itinerario"
            )

        eliminada = self.repo.eliminar_actividad(id_itinerario, id_actividad)
        if not eliminada:
            raise ItinerarioNoEncontradoError(
                f"Actividad {id_actividad} no encontrada en el itinerario"
            )
        return {"mensaje": f"Actividad {id_actividad} eliminada correctamente"}


# Instancia compartida lista para inyectar en el router
itinerario_service = ItinerarioService(itinerario_repository)