"""Generacion de pistas sobre la posicion de la bala.

Por defecto las pistas son veraces: describen la posicion actual de la
bala de una forma indirecta, para que el jugador vaya acotando donde esta
y deduciendo el patron de movimiento del tambor a partir de como cambian
de una pista a la siguiente. El evento "tambor_caliente" (ver eventos.py)
puede pedir una pista mentirosa con `mentir=True`: el texto es el mismo,
pero describe justo lo contrario de donde esta la bala.
"""

import random

TIPOS_PISTA = ("paridad", "mitad", "relativa")


def generar_pista(
    posicion_bala: int,
    huecos: int,
    ultimo_disparo: int | None,
    tipo: str | None = None,
    mentir: bool = False,
    rng: random.Random | None = None,
) -> str:
    """Devuelve un texto de pista sobre `posicion_bala`.

    Si no se indica `tipo`, se sortea uno entre los disponibles; la pista
    "relativa" (respecto al ultimo disparo) solo puede salir si ya hubo
    algun disparo previo en la partida. Con `mentir=True` la pista afirma
    lo opuesto de lo que es cierto (sigue siendo del mismo tipo y con el
    mismo aspecto: no hay forma de distinguirla salvo por el evento que la
    provoco).
    """
    generador = rng or random

    if tipo is None:
        disponibles = list(TIPOS_PISTA)
        if ultimo_disparo is None:
            disponibles.remove("relativa")
        tipo = generador.choice(disponibles)

    if tipo == "paridad":
        par = posicion_bala % 2 == 0
        if mentir:
            par = not par
        if par:
            return "La bala descansa en un hueco par."
        return "La bala no esta en los huecos pares."

    if tipo == "mitad":
        izquierda = posicion_bala <= huecos // 2
        if mentir:
            izquierda = not izquierda
        if izquierda:
            return "La bala esta en la mitad izquierda del tambor."
        return "La bala esta en la mitad derecha del tambor."

    if tipo == "relativa":
        if ultimo_disparo is None:
            raise ValueError("No hay disparo previo para dar una pista relativa.")
        if posicion_bala == ultimo_disparo:
            # No deberia ocurrir en la practica: si coincidieran habria
            # sido un impacto y la partida ya habria terminado antes de
            # pedir pista. `mentir` no tiene un opuesto claro aqui.
            return "La bala esta justo donde acabas de disparar."
        izquierda = posicion_bala < ultimo_disparo
        if mentir:
            izquierda = not izquierda
        if izquierda:
            return "La bala esta a la izquierda de tu ultimo disparo."
        return "La bala esta a la derecha de tu ultimo disparo."

    raise ValueError(f"Tipo de pista desconocido: {tipo}")
