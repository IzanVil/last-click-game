"""Semilla de partida: el numero que hace repetible una partida entera.

Toda la logica que sortea algo (el tambor y su patron, el tipo de pista,
los eventos, las frases de ambiente) acepta ya un `random.Random`; lo
que faltaba era un sitio donde nazca ese generador y un numero corto que
el jugador pueda apuntar y volver a teclear. Eso es este modulo: no
juega a nada, solo convierte una semilla en un generador y al reves.

La semilla es de la PARTIDA, no de la sesion: si fuese de la sesion, la
que se muestra al terminar solo serviria para repetir desde la primera,
y lo que uno quiere repetir es justo la partida que acaba de vivir -sea
la quinta seguida- o la que acaba de destapar un fallo.

Esto sustituye al `random.seed(args.seed)` que hacia main(): sembrar el
generador global fijaba la sesion entera y no dejaba forma de recuperar
la semilla de una partida ya jugada, que es lo que hace falta para
compartirla o para reproducir un fallo a posteriori. `--seed N` sigue
dando exactamente la misma primera partida que daba antes -- la
secuencia de Mersenne Twister es la misma se siembre el generador
global o uno propio -- asi que nadie pierde la partida que tenga
apuntada.
"""

import random

# Rango de semillas: 32 bits sin signo. Es corto de teclear a mano y
# cabe de sobra en el `seed` de RandomNumberGenerator (int64), para que
# la version de Godot pueda aceptar el mismo numero.
MAXIMO = 2**32 - 1


def nueva(rng: random.Random | None = None) -> int:
    """Sortea una semilla nueva dentro del rango valido."""
    generador = rng or random
    return generador.randint(0, MAXIMO)


def generador(valor: int) -> random.Random:
    """Devuelve el generador de una partida a partir de su semilla.

    Un `random.Random` propio, y no `random.seed()` sobre el generador
    global: sembrar el global haria que cualquier otro `random.*` del
    proceso consumiese numeros de esta misma secuencia y la partida
    dejaria de ser repetible por detras.
    """
    return random.Random(valor)
