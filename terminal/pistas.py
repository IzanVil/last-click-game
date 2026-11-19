import random
from collections.abc import Callable
from typing import NamedTuple

TIPOS_PISTA = ("paridad", "mitad", "relativa")


class Pista(NamedTuple):
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
    generador = rng or random

    if tipo is None:
        disponibles = list(TIPOS_PISTA)
        if ultimo_disparo is None:
            disponibles.remove("relativa")
        tipo = generador.choice(disponibles)

    if tipo == "paridad":
        return _pista_paridad(posicion_bala, huecos, mentir)
    if tipo == "mitad":
        return _pista_mitad(posicion_bala, huecos, mentir)
    if tipo == "relativa":
        if ultimo_disparo is None:
            raise ValueError("No hay disparo previo para dar una pista relativa.")
        return _pista_relativa(
            posicion_bala, huecos, ultimo_disparo, mentir, generador.choice
        )
    raise ValueError(f"Tipo de pista desconocido: {tipo}")


def _pista_paridad(posicion_bala: int, huecos: int, mentir: bool) -> Pista:
    rango = range(1, huecos + 1)
    par = (posicion_bala % 2 == 0) != mentir
    if par:
        return Pista(
            "La bala descansa en un hueco par.",
            frozenset(h for h in rango if h % 2 == 0),
        )
    return Pista(
        "La bala no esta en los huecos pares.",
        frozenset(h for h in rango if h % 2 != 0),
    )


def _pista_mitad(posicion_bala: int, huecos: int, mentir: bool) -> Pista:
    rango = range(1, huecos + 1)
    mitad = huecos // 2
    izquierda = (posicion_bala <= mitad) != mentir
    if izquierda:
        return Pista(
            "La bala esta en la mitad izquierda del tambor.",
            frozenset(h for h in rango if h <= mitad),
        )
    return Pista(
        "La bala esta en la mitad derecha del tambor.",
        frozenset(h for h in rango if h > mitad),
    )


def _pista_relativa(
    posicion_bala: int,
    huecos: int,
    ultimo_disparo: int,
    mentir: bool,
    elegir: Callable[[list[str]], str],
) -> Pista:
    if posicion_bala == ultimo_disparo:
        if not mentir:
            return Pista(
                "La bala esta justo donde acabas de disparar.",
                frozenset({ultimo_disparo}),
            )
        izquierda = _lado_al_azar(huecos, ultimo_disparo, elegir)
    else:
        izquierda = (posicion_bala < ultimo_disparo) != mentir

    rango = range(1, huecos + 1)
    if izquierda:
        return Pista(
            "La bala esta a la izquierda de tu ultimo disparo.",
            frozenset(h for h in rango if h < ultimo_disparo),
        )
    return Pista(
        "La bala esta a la derecha de tu ultimo disparo.",
        frozenset(h for h in rango if h > ultimo_disparo),
    )


def _lado_al_azar(
    huecos: int, ultimo_disparo: int, elegir: Callable[[list[str]], str]
) -> bool:
    lados = []
    if ultimo_disparo > 1:
        lados.append("izquierda")
    if ultimo_disparo < huecos:
        lados.append("derecha")
    return elegir(lados) == "izquierda"


def interseccion(pistas_reveladas: list[Pista]) -> frozenset[int]:
    if not pistas_reveladas:
        return frozenset()
    resultado = pistas_reveladas[0].candidatos
    for pista in pistas_reveladas[1:]:
        resultado = resultado & pista.candidatos
    return resultado
