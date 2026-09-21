"""Las reglas de una partida de "El Tambor del Juicio", sin pantalla.

Hermano de 2d/RuletaEstado.gd. Aqui vive lo que pasa cuando se dispara,
se marca o uno se retira; como se cuenta eso al jugador es cosa de la
interfaz (ruleta.py en la terminal, MainGame.gd en Godot).

La diferencia de forma con el hermano de Godot es solo idiomatica: alli
las cosas que pasan se emiten como señales y aqui se devuelven como una
lista de sucesos, porque en Python un valor de retorno se testea sin
montar un receptor. Los nombres son los mismos a proposito.

"Suceso" y no "evento": en este juego un evento es una cosa muy
concreta (el clic metalico y el tambor caliente, ver eventos.py), y
llamar igual a las dos se prestaba a confusion.

Una diferencia con el hermano que NO es un descuido: aqui un disparo
sobrevivido se cuenta antes que el evento que venga detras (es el orden
en que ocurren), mientras que RuletaEstado.gd emite `disparo_sobrevivido`
el ultimo porque ese manejador es ademas el que devuelve el control al
jugador, y adelantarlo le dejaria pulsar botones mientras corre el
cartel del evento. Es una restriccion de la interfaz grafica, no una
regla distinta: si algun dia se comparan las dos versiones partida a
partida, hay que comparar lo que pasa, no en que orden se cuenta.

Lo que NO hace este modulo, para que siga siendo solo reglas:

- No toca disco. Los records los carga y guarda quien escuche el final
  de la partida, igual que en la version de Godot.
- No escribe la bitacora de acciones (`historial.registrar_accion`), que
  es texto para un panel. Si lleva los contadores que alimentan el
  resumen final (faroles y eventos), que si son parte de la partida.
"""

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
        semillas,
    )
except ImportError:  # pragma: no cover - ejecucion como script suelto
    import apuestas  # type: ignore[no-redef,import-not-found]
    import estado  # type: ignore[no-redef,import-not-found]
    import eventos  # type: ignore[no-redef,import-not-found]
    import farol  # type: ignore[no-redef,import-not-found]
    import historial  # type: ignore[no-redef,import-not-found]
    import jugador  # type: ignore[no-redef,import-not-found]
    import pistas  # type: ignore[no-redef,import-not-found]
    import semillas  # type: ignore[no-redef,import-not-found]

APUESTA_BASE = 100
BONO_MARCA_ACERTADA = 50


class EntradaInvalida(NamedTuple):
    """Se pidio un hueco que no esta en el tambor."""

    numero: int


class EventoTambor(NamedTuple):
    """Ocurrio un evento aleatorio tras un disparo sobrevivido."""

    tipo: str
    texto: str


class DisparoSobrevivido(NamedTuple):
    """Un disparo real fallo (sobrevive): la apuesta se dobla."""

    disparos: int
    en_juego: int


class PistaNueva(NamedTuple):
    """Una pista mas, la del disparo que se acaba de sobrevivir."""

    numero: int
    pista: "pistas.Pista"


class DiaCompletado(NamedTuple):
    """Se completo un dia (cada DISPAROS_POR_DIA disparos sobrevividos)."""

    dia: int


class FarolResuelto(NamedTuple):
    """Se gasto una marca declarando un hueco seguro, acierte o falle."""

    hueco: int
    acierto: bool
    en_juego: int
    marcas_restantes: int
    bono: int


class Impacto(NamedTuple):
    """Un disparo real encontro la bala. Fin de la partida."""

    disparos: int
    perdidos: int
    dias: int
    resumen: str


class Retirada(NamedTuple):
    """El jugador cobro lo que tenia en juego. Fin de la partida."""

    disparos: int
    ganados: int
    dias: int
    resumen: str


class TurnoCambiado(NamedTuple):
    """Solo en duelo: el turno pasa al otro jugador."""

    nombre: str
    rival_nombre: str
    rival_dias: int


class DueloTerminado(NamedTuple):
    """Solo en duelo: tras el final, con los jugadores ya comparados."""

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
    """Una partida en curso: el tambor compartido y quienes lo juegan.

    Se construye ya empezada (no hay un `iniciar()` aparte): una partida
    nueva es un Motor nuevo, que es lo que hace que reiniciar no pueda
    dejarse a medias ningun contador del anterior.
    """

    def __init__(
        self,
        huecos: int = estado.HUECOS,
        marcas: int = farol.MARCAS_INICIALES,
        nombres: list[str] | None = None,
        semilla: int | None = None,
        probabilidad_eventos: float = eventos.PROBABILIDAD,
    ) -> None:
        self.semilla = semilla if semilla is not None else semillas.nueva()
        self.azar: random.Random = semillas.generador(self.semilla)
        self.probabilidad_eventos = probabilidad_eventos

        self.tambor = estado.TamborJuicio(huecos=huecos, rng=self.azar)
        self.pistas_reveladas: list[pistas.Pista] = []
        self.turno = 0
        self.terminada = False

        # Sin nombres, un unico jugador sin nombre: la partida en
        # solitario es un duelo de uno (ver jugador.py).
        self.jugadores = [
            jugador.Jugador(nombre, apuestas.Apuesta(APUESTA_BASE), farol.Farol(marcas))
            for nombre in (nombres or [""])
        ]

    # --- Atajos al jugador activo -------------------------------------
    #
    # En solitario "el jugador" es el unico que hay, asi que la interfaz
    # lee motor.apuesta, motor.disparos... sin tener que saber si esto
    # es un duelo o no.

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
        """Una partida en solitario es un duelo de un solo jugador, asi
        que "es un duelo" es simplemente "hay mas de uno"."""
        return len(self.jugadores) > 1

    def candidatos(self) -> frozenset[int]:
        """Huecos que siguen en pie tras cruzar todas las pistas."""
        return pistas.interseccion(self.pistas_reveladas)

    def marcadas(self) -> set[int]:
        """Huecos a los que ya se ha disparado en esta partida."""
        return set(self.tambor.historial)

    # --- Acciones -----------------------------------------------------

    def disparar(self, numero: int) -> list[Suceso]:
        """Resuelve un disparo real a `numero`.

        Devuelve todo lo que pasa a raiz de el, en el orden en que se
        cuenta: primero lo que hizo el tambor, luego como te fue, luego
        lo que has aprendido, y por ultimo el cambio de dia o de turno.
        """
        if not 1 <= numero <= self.tambor.huecos:
            return [EntradaInvalida(numero)]

        activo = self.jugador_activo
        activo.disparos += 1

        if self.tambor.disparar(numero):
            # Apuesta.perder() devuelve la cantidad PERDIDA, asi que al
            # morir `puntos_finales` guarda lo que se dejo en la mesa y
            # no un 0. Se conserva porque es lo que hacian ya las dos
            # versiones (y de ahi sale el "perdiendo N puntos" de la
            # pantalla final), pero tiene dos efectos discutibles: en un
            # duelo empatado a dias, morir con un bote gordo gana a
            # retirarse con poco (ver jugador.ganadores), y los records
            # apuntan como "puntos maximos" unos puntos que nadie cobro.
            # Cambiarlo cambia quien gana partidas, asi que no se toca
            # aqui: este modulo mueve las reglas de sitio, no las
            # reescribe.
            activo.puntos_finales = activo.apuesta.perder()
            return self._terminar(
                Impacto(
                    activo.disparos,
                    activo.puntos_finales,
                    activo.dias,
                    historial.resumen(activo.bitacora, activo.dias),
                )
            )

        activo.apuesta.doblar()
        # Orden cronologico, que es el mismo en el que ocurren aqui
        # arriba: sobrevives, entonces el tambor hace de las suyas, y
        # solo despues llega la pista. La version de terminal apuntaba
        # en su bitacora "disparo" antes que "evento" pero los pintaba
        # al reves en pantalla; con un unico orden dejan de poder
        # discrepar.
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
        """Gasta una marca declarando `hueco` como seguro.

        Nunca mueve la bala ni termina la partida: solo dice si el
        jugador acerto (ver farol.py). En duelo si consume el turno,
        igual que en la version grafica.
        """
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
        """Cobra los puntos en juego y termina la partida."""
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

    # --- Tripas -------------------------------------------------------

    def _avanzar_turno(self) -> list[Suceso]:
        """Pasa el turno tras un disparo sobrevivido o un farol.

        No se llama tras un impacto o una retirada, que terminan la
        partida entera. En solitario el turno tambien avanza: cuenta
        acciones, y el jugador activo sigue siendo el unico que hay.
        """
        self.turno += 1
        if not self.es_duelo():
            return []
        activo = self.jugador_activo
        rival = self.jugadores[(self.turno + 1) % len(self.jugadores)]
        return [TurnoCambiado(activo.nombre, rival.nombre, rival.dias)]

    def _terminar(self, final: Impacto | Retirada) -> list[Suceso]:
        """Cierra la partida y, si era un duelo, reparte el veredicto.

        El duelo acaba en cuanto el turno de uno de los dos termina en
        impacto o en retirada: el otro no sigue jugando en solitario
        despues, asi que ni perdio ni cobro y se queda con lo que tenia
        en juego en ese momento.
        """
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
