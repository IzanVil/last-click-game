MARCAS_INICIALES = 3


class Farol:
    def __init__(self, marcas: int = MARCAS_INICIALES) -> None:
        if marcas < 0:
            raise ValueError("El numero de marcas no puede ser negativo.")
        self.marcas_restantes = marcas

    def puede_marcar(self) -> bool:
        return self.marcas_restantes > 0

    def marcar(self, hueco: int, posicion_bala: int) -> bool:
        if not self.puede_marcar():
            raise ValueError("No quedan marcas disponibles.")
        self.marcas_restantes -= 1
        return hueco != posicion_bala
