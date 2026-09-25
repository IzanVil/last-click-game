"""Un jugador dentro de una partida: apuesta, marcas, historial y disparos.

Hermano de 2d/Jugador.gd. Vale igual para la partida en solitario, que
es -- aqui y alli -- un duelo de un unico jugador: asi el motor tiene un
solo camino en vez de dos parecidos (ver motor.py).

El tambor, su patron y las pistas NO viven aqui: son compartidos por
todos los jugadores de la partida y los lleva el motor. En un duelo es
literalmente el mismo revolver.
"""

from dataclasses import dataclass, field

try:
    from . import apuestas, estado, farol, historial
except ImportError:  # pragma: no cover - ejecucion como script suelto
    import apuestas  # type: ignore[no-redef,import-not-found]
    import estado  # type: ignore[no-redef,import-not-found]
    import farol  # type: ignore[no-redef,import-not-found]
    import historial  # type: ignore[no-redef,import-not-found]


@dataclass
class Jugador:
    """Lo que es propio de cada jugador y no se comparte en un duelo."""

    nombre: str
    apuesta: "apuestas.Apuesta"
    marca: "farol.Farol"
    bitacora: "historial.Historial" = field(default_factory=historial.Historial)
    disparos: int = 0

    # Si la bala lo encontro. `disparos` sigue contando el tiro fatal
    # -- se apreto el gatillo, y de ahi sale el "caiste tras N
    # disparo(s)" de la pantalla final -- pero ese tiro no se
    # sobrevivio, asi que no cuenta para los dias.
    murio: bool = False

    # Puntos con los que este jugador termina la partida. Lo fija el
    # motor al morir (0), al retirarse (lo cobrado) o, para el rival que
    # no llego a jugar su ultimo turno, lo que tuviera en juego.
    puntos_finales: int = 0

    @property
    def dias(self) -> int:
        """Dias completos que lleva sobrevividos este jugador."""
        return estado.dias_sobrevividos(self.disparos - (1 if self.murio else 0))


def ganadores(jugadores: list[Jugador]) -> list[Jugador]:
    """Decide quien gana: mandan los dias, y desempatan los puntos.

    Devuelve una lista porque un empate total (mismos dias y mismos
    puntos) no tiene un ganador unico. Hermano de Jugador.ganadores().
    """
    if not jugadores:
        return []

    mejor_dias = max(j.dias for j in jugadores)
    finalistas = [j for j in jugadores if j.dias == mejor_dias]
    if len(finalistas) == 1:
        return finalistas

    mejores_puntos = max(j.puntos_finales for j in finalistas)
    return [j for j in finalistas if j.puntos_finales == mejores_puntos]
