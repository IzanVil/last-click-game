import random
from typing import NamedTuple

try:
    from . import (
        apuestas,
        estado,
        eventos,
        farol,
        historial,
        jugador,
        pistas,
    )
except ImportError:  # pragma: no cover
    import apuestas  # type: ignore[no-redef,import-not-found]
    import estado  # type: ignore[no-redef,import-not-found]
    import eventos  # type: ignore[no-redef,import-not-found]
    import farol  # type: ignore[no-redef,import-not-found]
    import historial  # type: ignore[no-redef,import-not-found]
    import jugador  # type: ignore[no-redef,import-not-found]
    import pistas  # type: ignore[no-redef,import-not-found]

APUESTA_BASE = 100
BONO_MARCA_ACERTADA = 50


class EntradaInvalida(NamedTuple):
    numero: int


class EventoTambor(NamedTuple):
    tipo: str
    texto: str


class DisparoSobrevivido(NamedTuple):
    disparos: int
    en_juego: int


class PistaNueva(NamedTuple):
    numero: int
    pista: "pistas.Pista"


class DiaCompletado(NamedTuple):
    dia: int


class FarolResuelto(NamedTuple):
    hueco: int
    acierto: bool
    en_juego: int
    marcas_restantes: int
    bono: int


class Impacto(NamedTuple):
    disparos: int
    perdidos: int
    dias: int
    resumen: str


class Retirada(NamedTuple):
    disparos: int
    ganados: int
    dias: int
    resumen: str


class TurnoCambiado(NamedTuple):
    nombre: str
    rival_nombre: str
    rival_dias: int


class DueloTerminado(NamedTuple):
    jugadores: list["jugador.Jugador"]
    ganadores: list["jugador.Jugador"]


Suceso = (
    EntradaInvalida
    | EventoTambor
    | DisparoSobrevivido
    | PistaNueva
    | DiaCompletado
    | FarolResuelto
    | Impacto
    | Retirada
    | TurnoCambiado
    | DueloTerminado
)


class Motor:
    def __init__(
        self,
        huecos: int = estado.HUECOS,
        marcas: int = farol.MARCAS_INICIALES,
        nombres: list[str] | None = None,
        rng: random.Random | None = None,
        probabilidad_eventos: float = eventos.PROBABILIDAD,
    ) -> None:
        self.azar = rng
        self.probabilidad_eventos = probabilidad_eventos

        self.tambor = estado.TamborJuicio(huecos=huecos, rng=self.azar)
        self.pistas_reveladas: list[pistas.Pista] = []
        self.turno = 0
        self.terminada = False

        self.jugadores = [
            jugador.Jugador(nombre, apuestas.Apuesta(APUESTA_BASE), farol.Farol(marcas))
            for nombre in (nombres or [""])
        ]

    @property
    def jugador_activo(self) -> "jugador.Jugador":
        return self.jugadores[self.turno % len(self.jugadores)]

    @property
    def apuesta(self) -> "apuestas.Apuesta":
        return self.jugador_activo.apuesta

    @property
    def marca(self) -> "farol.Farol":
        return self.jugador_activo.marca

    @property
    def bitacora(self) -> "historial.Historial":
        return self.jugador_activo.bitacora

    @property
    def disparos(self) -> int:
        return self.jugador_activo.disparos

    @property
    def huecos(self) -> int:
        return self.tambor.huecos

    def es_duelo(self) -> bool:
        return len(self.jugadores) > 1

    def candidatos(self) -> frozenset[int]:
        return pistas.interseccion(self.pistas_reveladas)

    def marcadas(self) -> set[int]:
        return set(self.tambor.historial)

    def disparar(self, numero: int) -> list[Suceso]:
        if not 1 <= numero <= self.tambor.huecos:
            return [EntradaInvalida(numero)]

        activo = self.jugador_activo
        activo.disparos += 1

        if self.tambor.disparar(numero):
            activo.murio = True
            perdidos = activo.apuesta.perder()
            activo.puntos_finales = 0
            return self._terminar(
                Impacto(
                    activo.disparos,
                    perdidos,
                    activo.dias,
                    historial.resumen(activo.bitacora, activo.dias),
                )
            )

        activo.apuesta.doblar()
        sucesos: list[Suceso] = [
            DisparoSobrevivido(activo.disparos, activo.apuesta.en_juego)
        ]

        evento = eventos.tirar_evento(self.probabilidad_eventos, rng=self.azar)
        if evento is not None:
            if evento == "clic_metalico":
                self.tambor.mover_extra()
            activo.bitacora.registrar_evento(evento)
            sucesos.append(EventoTambor(evento, eventos.texto_de(evento)))

        pista = pistas.generar_pista(
            self.tambor.posicion_bala,
            self.tambor.huecos,
            self.tambor.ultimo_disparo,
            mentir=(evento == "tambor_caliente"),
            rng=self.azar,
        )
        self.pistas_reveladas.append(pista)
        sucesos.append(PistaNueva(len(self.pistas_reveladas), pista))

        if activo.disparos % estado.DISPAROS_POR_DIA == 0:
            sucesos.append(DiaCompletado(activo.dias))

        sucesos.extend(self._avanzar_turno())
        return sucesos

    def marcar(self, hueco: int) -> list[Suceso]:
        if not 1 <= hueco <= self.tambor.huecos:
            return [EntradaInvalida(hueco)]

        activo = self.jugador_activo
        acierto = activo.marca.marcar(hueco, self.tambor.posicion_bala)
        activo.bitacora.registrar_farol(acierto)
        bono = BONO_MARCA_ACERTADA if acierto else 0
        if acierto:
            activo.apuesta.sumar_bono(bono)

        sucesos: list[Suceso] = [
            FarolResuelto(
                hueco,
                acierto,
                activo.apuesta.en_juego,
                activo.marca.marcas_restantes,
                bono,
            )
        ]
        sucesos.extend(self._avanzar_turno())
        return sucesos

    def retirarse(self) -> list[Suceso]:
        activo = self.jugador_activo
        activo.puntos_finales = activo.apuesta.retirarse()
        return self._terminar(
            Retirada(
                activo.disparos,
                activo.puntos_finales,
                activo.dias,
                historial.resumen(activo.bitacora, activo.dias),
            )
        )

    def _avanzar_turno(self) -> list[Suceso]:
        self.turno += 1
        if not self.es_duelo():
            return []
        activo = self.jugador_activo
        rival = self.jugadores[(self.turno + 1) % len(self.jugadores)]
        return [TurnoCambiado(activo.nombre, rival.nombre, rival.dias)]

    def _terminar(self, final: Impacto | Retirada) -> list[Suceso]:
        self.terminada = True
        if not self.es_duelo():
            return [final]

        activo = self.jugador_activo
        for otro in self.jugadores:
            if otro is not activo:
                otro.puntos_finales = otro.apuesta.en_juego
        return [
            final,
            DueloTerminado(self.jugadores, jugador.ganadores(self.jugadores)),
        ]
