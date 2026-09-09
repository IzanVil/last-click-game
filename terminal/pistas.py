"""Generacion de pistas sobre la posicion de la bala.

Por defecto las pistas son veraces: describen la posicion actual de la
bala de una forma indirecta, para que el jugador vaya acotando donde esta
y deduciendo el patron de movimiento del tambor a partir de como cambian
de una pista a la siguiente. El evento "tambor_caliente" (ver eventos.py)
puede pedir una pista mentirosa con `mentir=True`: el texto es el mismo,
pero describe justo lo contrario de donde esta la bala.

Cada pista lleva ademas, en `candidatos`, el conjunto de huecos que esa
misma afirmacion deja como posibles (los que no descarta). No indica
donde esta la bala: son solo los huecos consistentes con lo que la pista
dice, para poder resaltarlos en el tambor (ver ruleta.py). Cruzando los
candidatos de varias pistas se acota el rango... o, si una es mentira, se
nota que algo no cuadra cuando el cruce se queda vacio.
"""

import random
from typing import NamedTuple

TIPOS_PISTA = ("paridad", "mitad", "relativa")


class Pista(NamedTuple):
    """Una pista: su texto y los huecos que esa afirmacion deja en pie."""

    texto: str
    candidatos: frozenset[int]


def generar_pista(
    posicion_bala: int,
    huecos: int,
    ultimo_disparo: int | None,
    tipo: str | None = None,
    mentir: bool = False,
    rng: random.Random | None = None,
) -> Pista:
    """Devuelve una `Pista` sobre `posicion_bala`.

    Si no se indica `tipo`, se sortea uno entre los disponibles; la pista
    "relativa" (respecto al ultimo disparo) solo puede salir si ya hubo
    algun disparo previo en la partida. Con `mentir=True` la pista afirma
    lo opuesto de lo que es cierto (mismo tipo y aspecto; sus candidatos
    tambien cambian, porque son los huecos que esa afirmacion respalda,
    no los que de verdad son ciertos).
    """
    generador = rng or random
    rango = range(1, huecos + 1)

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
            return Pista(
                "La bala descansa en un hueco par.",
                frozenset(h for h in rango if h % 2 == 0),
            )
        return Pista(
            "La bala no esta en los huecos pares.",
            frozenset(h for h in rango if h % 2 != 0),
        )

    if tipo == "mitad":
        mitad = huecos // 2
        izquierda = posicion_bala <= mitad
        if mentir:
            izquierda = not izquierda
        if izquierda:
            return Pista(
                "La bala esta en la mitad izquierda del tambor.",
                frozenset(h for h in rango if h <= mitad),
            )
        return Pista(
            "La bala esta en la mitad derecha del tambor.",
            frozenset(h for h in rango if h > mitad),
        )

    if tipo == "relativa":
        if ultimo_disparo is None:
            raise ValueError("No hay disparo previo para dar una pista relativa.")
        if posicion_bala == ultimo_disparo:
            # Ocurre de verdad, y ni siquiera es raro: la bala se mueve
            # DESPUES de un disparo fallido (ver TamborJuicio.disparar),
            # asi que puede acabar justo en el hueco que se acaba de
            # probar. Con el patron "avanza" basta con disparar un hueco
            # por delante de ella. Aqui `mentir` si tiene un opuesto
            # claro: si la bala esta exactamente en el ultimo disparo,
            # cualquiera de los dos lados es falso. Antes esta rama lo
            # ignoraba, de modo que un evento "tambor_caliente" -que
            # existe justo para mentir- acababa regalando la posicion
            # exacta de la bala.
            if not mentir:
                return Pista(
                    "La bala esta justo donde acabas de disparar.",
                    frozenset({ultimo_disparo}),
                )
            # Se miente hacia un lado que exista: disparar al hueco 1 (o
            # al ultimo) deja un lado sin ningun hueco, y una pista con
            # cero candidatos se delataria sola al cruzarla.
            lados = []
            if ultimo_disparo > 1:
                lados.append("izquierda")
            if ultimo_disparo < huecos:
                lados.append("derecha")
            izquierda = generador.choice(lados) == "izquierda"
            if izquierda:
                return Pista(
                    "La bala esta a la izquierda de tu ultimo disparo.",
                    frozenset(h for h in rango if h < ultimo_disparo),
                )
            return Pista(
                "La bala esta a la derecha de tu ultimo disparo.",
                frozenset(h for h in rango if h > ultimo_disparo),
            )
        izquierda = posicion_bala < ultimo_disparo
        if mentir:
            izquierda = not izquierda
        if izquierda:
            return Pista(
                "La bala esta a la izquierda de tu ultimo disparo.",
                frozenset(h for h in rango if h < ultimo_disparo),
            )
        return Pista(
            "La bala esta a la derecha de tu ultimo disparo.",
            frozenset(h for h in rango if h > ultimo_disparo),
        )

    raise ValueError(f"Tipo de pista desconocido: {tipo}")


def interseccion(pistas_reveladas: list[Pista]) -> frozenset[int]:
    """Cruza los candidatos de varias pistas.

    Vacio si todavia no hay ninguna pista, o si las que hay se contradicen
    entre si (senal de que alguna, por un evento "tambor_caliente", pudo
    ser mentira).
    """
    if not pistas_reveladas:
        return frozenset()
    resultado = pistas_reveladas[0].candidatos
    for pista in pistas_reveladas[1:]:
        resultado = resultado & pista.candidatos
    return resultado
