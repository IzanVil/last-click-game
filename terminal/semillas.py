import random

MAXIMO = 2**32 - 1


def nueva(rng: random.Random | None = None) -> int:
    generador = rng or random
    return generador.randint(0, MAXIMO)


def generador(valor: int) -> random.Random:
    return random.Random(valor)
