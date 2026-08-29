"""Estado y logica pura de "El Tambor del Juicio" (sin entrada/salida).

Este modulo no imprime nada ni lee del teclado: solo lleva el tambor, la
posicion de la bala y su movimiento. La interfaz (ruleta.py) es quien
decide como mostrarlo y como pedir la siguiente accion al jugador.
"""

import random

HUECOS = 8

# Cuantos disparos sobrevividos forman un "dia de vida" (el objetivo de la
# Fase 2: la partida no acaba al perder, se cuenta cuanto se ha aguantado).
DISPAROS_POR_DIA = 3

# Patrones de movimiento de la bala tras un disparo fallido (que no la
# encuentra). Se sortea uno al iniciar la partida y se mantiene oculto:
# el jugador debe deducirlo a partir de las pistas que va recibiendo.
PATRONES = ("avanza", "retrocede", "salta_dos", "espejo")


def dias_sobrevividos(
    disparos_superados: int, disparos_por_dia: int = DISPAROS_POR_DIA
) -> int:
    """Cuenta cuantos dias completos (de `disparos_por_dia` disparos) se han
    sobrevivido. Un dia en curso, aun sin terminar, no cuenta todavia."""
    return disparos_superados // disparos_por_dia


def _mover(posicion: int, patron: str, huecos: int) -> int:
    """Calcula la nueva posicion de la bala tras aplicar `patron`."""
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
    """Tambor con una unica bala que se desplaza tras cada disparo fallido.

    "Fallido" se entiende desde el punto de vista de la bala: un disparo
    que no la encuentra. El patron de movimiento (`self.patron`) se sortea
    al construir el tambor y no cambia durante la partida.
    """

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
        """Resuelve un disparo a `numero`. Devuelve True si impacta en la bala.

        Si no impacta, la bala se desplaza segun `self.patron` antes de
        devolver el control: la siguiente pista y el siguiente disparo ya
        veran la posicion nueva.
        """
        if not 1 <= numero <= self.huecos:
            raise ValueError(f"Posicion fuera de rango: {numero}")

        self.ultimo_disparo = numero
        self.historial.append(numero)

        impacto = numero == self.posicion_bala
        if not impacto:
            self.posicion_bala = _mover(self.posicion_bala, self.patron, self.huecos)
        return impacto

    def mover_extra(self) -> int:
        """Desplaza la bala una vez mas, fuera de un disparo.

        Lo dispara un evento aleatorio (ver eventos.py) para simular que
        el tambor se ha movido solo entre disparo y disparo. Reutiliza el
        mismo patron de movimiento que un fallo normal.
        """
        self.posicion_bala = _mover(self.posicion_bala, self.patron, self.huecos)
        return self.posicion_bala
