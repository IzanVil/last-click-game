"""Sistema de apuestas de "El Tambor del Juicio": doblar o retirarse.

La partida arranca con una apuesta base ya "en juego". Tras cada disparo
que sobrevive, los puntos en juego se doblan; el jugador decide en cada
turno si se retira (cobra lo que hay en juego) o sigue arriesgando el
doble de esos mismos puntos.
"""


class Apuesta:
    """Puntos en juego durante la partida actual."""

    def __init__(self, base: int) -> None:
        if base <= 0:
            raise ValueError("La apuesta base debe ser un entero positivo.")
        self.base = base
        self.en_juego = base

    def doblar(self) -> int:
        """Duplica los puntos en juego tras sobrevivir un disparo."""
        self.en_juego *= 2
        return self.en_juego

    def perder(self) -> int:
        """Pierde todos los puntos en juego. Devuelve la cantidad perdida."""
        perdidos = self.en_juego
        self.en_juego = 0
        return perdidos

    def retirarse(self) -> int:
        """Cierra la apuesta sin arriesgar mas. Devuelve lo que se cobra."""
        return self.en_juego
