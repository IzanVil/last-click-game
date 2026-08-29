"""Generacion de pistas veraces sobre la posicion de la bala.

Las pistas nunca mienten (esa distorsion queda para una fase futura, ver
README): describen la posicion actual de la bala de una forma indirecta,
para que el jugador vaya acotando donde esta y deduciendo el patron de
movimiento del tambor a partir de como cambian de una pista a la siguiente.
"""

import random

TIPOS_PISTA = ("paridad", "mitad", "relativa")


def generar_pista(
    posicion_bala: int,
    huecos: int,
    ultimo_disparo: int | None,
    tipo: str | None = None,
    rng: random.Random | None = None,
) -> str:
    """Devuelve un texto de pista veraz sobre `posicion_bala`.

    Si no se indica `tipo`, se sortea uno entre los disponibles; la pista
    "relativa" (respecto al ultimo disparo) solo puede salir si ya hubo
    algun disparo previo en la partida.
    """
    generador = rng or random

    if tipo is None:
        disponibles = list(TIPOS_PISTA)
        if ultimo_disparo is None:
            disponibles.remove("relativa")
        tipo = generador.choice(disponibles)

    if tipo == "paridad":
        if posicion_bala % 2 == 0:
            return "La bala descansa en un hueco par."
        return "La bala no esta en los huecos pares."

    if tipo == "mitad":
        mitad = huecos // 2
        if posicion_bala <= mitad:
            return "La bala esta en la mitad izquierda del tambor."
        return "La bala esta en la mitad derecha del tambor."

    if tipo == "relativa":
        if ultimo_disparo is None:
            raise ValueError("No hay disparo previo para dar una pista relativa.")
        if posicion_bala < ultimo_disparo:
            return "La bala esta a la izquierda de tu ultimo disparo."
        if posicion_bala > ultimo_disparo:
            return "La bala esta a la derecha de tu ultimo disparo."
        # No deberia ocurrir en la practica: si coincidieran habria sido
        # un impacto y la partida ya habria terminado antes de pedir pista.
        return "La bala esta justo donde acabas de disparar."

    raise ValueError(f"Tipo de pista desconocido: {tipo}")
