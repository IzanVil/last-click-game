import random

HUECOS = 8

DISPAROS_POR_DIA = 3

PATRONES = ("avanza", "retrocede", "salta_dos", "espejo")


def dias_sobrevividos(
    disparos_superados: int, disparos_por_dia: int = DISPAROS_POR_DIA
) -> int:
    return disparos_superados // disparos_por_dia


def _mover(posicion: int, patron: str, huecos: int) -> int:
    if patron == "avanza":
        return posicion % huecos + 1
    if patron == "retrocede":
        return (posicion - 2) % huecos + 1
    if patron == "salta_dos":
        return (posicion + 1) % huecos + 1
    if patron == "espejo":
        return huecos + 1 - posicion
    raise ValueError(f"Patron de movimiento desconocido: {patron}")


class TamborJuicio:
    def __init__(
        self,
        huecos: int = HUECOS,
        patron: str | None = None,
        posicion_inicial: int | None = None,
        rng: random.Random | None = None,
    ) -> None:
        if huecos < 2:
            raise ValueError("El tambor necesita al menos 2 huecos.")
        if patron is not None and patron not in PATRONES:
            raise ValueError(f"Patron de movimiento desconocido: {patron}")
        if posicion_inicial is not None and not 1 <= posicion_inicial <= huecos:
            raise ValueError(f"Posicion inicial fuera de rango: {posicion_inicial}")

        generador = rng or random
        self.huecos = huecos
        self.patron = patron or generador.choice(PATRONES)
        self.posicion_bala = posicion_inicial or generador.randint(1, huecos)
        self.ultimo_disparo: int | None = None
        self.historial: list[int] = []

    def disparar(self, numero: int) -> bool:
        if not 1 <= numero <= self.huecos:
            raise ValueError(f"Posicion fuera de rango: {numero}")

        self.ultimo_disparo = numero
        self.historial.append(numero)

        impacto = numero == self.posicion_bala
        if not impacto:
            self.posicion_bala = _mover(self.posicion_bala, self.patron, self.huecos)
        return impacto

    def mover_extra(self) -> int:
        self.posicion_bala = _mover(self.posicion_bala, self.patron, self.huecos)
        return self.posicion_bala
