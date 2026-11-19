class Apuesta:
    def __init__(self, base: int) -> None:
        if base <= 0:
            raise ValueError("La apuesta base debe ser un entero positivo.")
        self.base = base
        self.en_juego = base

    def doblar(self) -> int:
        self.en_juego *= 2
        return self.en_juego

    def perder(self) -> int:
        perdidos = self.en_juego
        self.en_juego = 0
        return perdidos

    def retirarse(self) -> int:
        return self.en_juego

    def sumar_bono(self, cantidad: int) -> int:
        self.en_juego += cantidad
        return self.en_juego
