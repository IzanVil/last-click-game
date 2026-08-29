"""Sistema de farol: marcar un hueco como seguro sin disparar.

Marcar consume una de las marcas disponibles en la partida (un recurso
limitado), acierte o falle. A diferencia de un disparo, marcar nunca
mueve la bala ni termina la partida: solo dice si el jugador acerto, para
que pueda validar una deduccion sin arriesgar el pellejo.
"""

MARCAS_INICIALES = 3


class Farol:
    """Marcas disponibles durante la partida actual."""

    def __init__(self, marcas: int = MARCAS_INICIALES) -> None:
        if marcas < 0:
            raise ValueError("El numero de marcas no puede ser negativo.")
        self.marcas_restantes = marcas

    def puede_marcar(self) -> bool:
        """Indica si quedan marcas disponibles para usar."""
        return self.marcas_restantes > 0

    def marcar(self, hueco: int, posicion_bala: int) -> bool:
        """Gasta una marca declarando `hueco` como seguro.

        Devuelve True si acierta (la bala no estaba ahi). Consume la
        marca tanto si acierta como si falla: es el coste de preguntar.
        """
        if not self.puede_marcar():
            raise ValueError("No quedan marcas disponibles.")
        self.marcas_restantes -= 1
        return hueco != posicion_bala
