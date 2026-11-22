from datetime import date, datetime
import re
from typing import Optional
from domain.vuelo import (
    BusquedaVuelosDataSchema,
    BusquedaVuelosResponseSchema,
    ValidacionVueloError,
    VueloItemSchema,
)
from repository.vuelo_repository import VueloRepository, vuelo_repository

IATA_REGEX = re.compile(r"^[A-Za-z]{3}$")


class VueloService:

    def __init__(self, repo: VueloRepository = vuelo_repository) -> None:
        self.repo = repo

    def _validar_iata(self, codigo: Optional[str], campo: str) -> str:
        if not codigo or not IATA_REGEX.match(codigo.strip()):
            raise ValidacionVueloError(
                f"El formato del código IATA de {campo} no es válido"
            )
        return codigo.strip().upper()

    def _validar_fecha_ida(self, fecha_str: Optional[str]) -> date:
        if not fecha_str or not fecha_str.strip():
            raise ValidacionVueloError("La fecha de ida es obligatoria")
        try:
            fecha = datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValidacionVueloError(
                "Error en el formato o vigencia de la fecha de ida (use YYYY-MM-DD)"
            ) from exc
        if fecha < date.today():
            raise ValidacionVueloError(
                "Error en el formato o vigencia de la fecha de ida: no puede ser anterior a la fecha actual"
            )
        return fecha

    def _validar_fecha_retorno(
        self, fecha_retorno_str: Optional[str], fecha_ida: date
    ) -> Optional[str]:
        if fecha_retorno_str is None:
            return None
        limpia = fecha_retorno_str.strip()
        if not limpia:
            return None
        try:
            fecha_ret = datetime.strptime(limpia, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValidacionVueloError(
                "Error en el formato o vigencia de la fecha de retorno (use YYYY-MM-DD)"
            ) from exc
        if fecha_ret < fecha_ida:
            raise ValidacionVueloError(
                "La fecha de retorno no puede ser anterior a la fecha de ida"
            )
        return limpia

    def buscar(
        self,
        origen: Optional[str],
        destino: Optional[str],
        fecha_ida: Optional[str],
        pasajeros: int = 1,
        fecha_retorno: Optional[str] = None,
    ) -> BusquedaVuelosResponseSchema:
        origen_limpio = self._validar_iata(origen, "origen")
        destino_limpio = self._validar_iata(destino, "destino")
        fecha_ida_dt = self._validar_fecha_ida(fecha_ida)
        fecha_retorno_limpia = self._validar_fecha_retorno(
            fecha_retorno, fecha_ida_dt
        )

        if pasajeros < 1:
            raise ValidacionVueloError(
                "El número de pasajeros debe ser mayor o igual a 1"
            )

        vuelos_encontrados = self.repo.buscar_vuelos(
            origen=origen_limpio,
            destino=destino_limpio,
            fecha_ida=fecha_ida_dt.isoformat(),
            pasajeros=pasajeros,
            fecha_retorno=fecha_retorno_limpia,
        )

        if not vuelos_encontrados:
            return BusquedaVuelosResponseSchema(
                message="No se encontraron vuelos disponibles para la ruta y fecha seleccionada",
                data=BusquedaVuelosDataSchema(total_resultados=0, vuelos=[]),
                success=False,
            )

        incluye_retorno = fecha_retorno_limpia is not None
        items = [
            VueloItemSchema(
                **vuelo.to_dict(
                    pasajeros=pasajeros, incluye_retorno=incluye_retorno
                )
            )
            for vuelo in vuelos_encontrados
        ]
        return BusquedaVuelosResponseSchema(
            message="Búsqueda de vuelos exitosa",
            data=BusquedaVuelosDataSchema(
                total_resultados=len(items),
                vuelos=items,
            ),
            success=True,
        )