from dataclasses import dataclass, field

try:
    from . import apuestas, estado, farol, historial
except ImportError:  # pragma: no cover
    import apuestas  # type: ignore[no-redef,import-not-found]
    import estado  # type: ignore[no-redef,import-not-found]
    import farol  # type: ignore[no-redef,import-not-found]
    import historial  # type: ignore[no-redef,import-not-found]


@dataclass
class Jugador:
    nombre: str
    apuesta: "apuestas.Apuesta"
    marca: "farol.Farol"
    bitacora: "historial.Historial" = field(default_factory=historial.Historial)
    disparos: int = 0

    murio: bool = False

    puntos_finales: int = 0

    @property
    def dias(self) -> int:
        return estado.dias_sobrevividos(self.disparos - (1 if self.murio else 0))


def ganadores(jugadores: list[Jugador]) -> list[Jugador]:
    if not jugadores:
        return []

    mejor_dias = max(j.dias for j in jugadores)
    finalistas = [j for j in jugadores if j.dias == mejor_dias]
    if len(finalistas) == 1:
        return finalistas

    mejores_puntos = max(j.puntos_finales for j in finalistas)
    return [j for j in finalistas if j.puntos_finales == mejores_puntos]
