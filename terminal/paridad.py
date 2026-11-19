import itertools
import json
import random
from collections.abc import Sequence
from pathlib import Path
from typing import Any

try:
    from . import (
        apuestas,
        estado,
        eventos,
        farol,
        historial,
        jugador,
        pistas,
        ruleta,
        semillas,
    )
except ImportError:  # pragma: no cover
    import apuestas  # type: ignore[no-redef,import-not-found]
    import estado  # type: ignore[no-redef,import-not-found]
    import eventos  # type: ignore[no-redef,import-not-found]
    import farol  # type: ignore[no-redef,import-not-found]
    import historial  # type: ignore[no-redef,import-not-found]
    import jugador  # type: ignore[no-redef,import-not-found]
    import pistas  # type: ignore[no-redef,import-not-found]
    import ruleta  # type: ignore[no-redef,import-not-found]
    import semillas  # type: ignore[no-redef,import-not-found]

FORMATO = 4

HUECOS_PROBADOS = (6, 8, 10)


def ruta_por_defecto() -> Path:
    return Path(__file__).resolve().parent.parent / "2d" / "tests" / "paridad.json"


def _constantes() -> dict:
    return {
        "huecos": estado.HUECOS,
        "disparos_por_dia": estado.DISPAROS_POR_DIA,
        "patrones": list(estado.PATRONES),
        "tipos_pista": list(pistas.TIPOS_PISTA),
        "tipos_evento": list(eventos.TIPOS_EVENTO),
        "textos_evento": dict(eventos.TEXTOS),
        "probabilidad_evento": eventos.PROBABILIDAD,
        "marcas_iniciales": farol.MARCAS_INICIALES,
        "apuesta_base": ruleta.APUESTA_BASE,
        "bono_marca_acertada": ruleta.BONO_MARCA_ACERTADA,
        "max_acciones": historial.MAX_ACCIONES,
        "semilla_maxima": semillas.MAXIMO,
        "dificultades": ruleta.DIFICULTADES,
    }


def _mover() -> list[dict]:
    casos = []
    for huecos in HUECOS_PROBADOS:
        for patron in estado.PATRONES:
            for posicion in range(1, huecos + 1):
                casos.append(
                    {
                        "huecos": huecos,
                        "patron": patron,
                        "posicion": posicion,
                        "resultado": estado._mover(posicion, patron, huecos),
                    }
                )
    return casos


def _dias() -> list[dict]:
    return [
        {"disparos": n, "resultado": estado.dias_sobrevividos(n)} for n in range(0, 13)
    ]


def _pista_a_dict(pista: "pistas.Pista") -> dict:
    return {"texto": pista.texto, "candidatos": sorted(pista.candidatos)}


class _RngFijo(random.Random):
    def __init__(self, indice: int) -> None:
        super().__init__()
        self.indice = indice

    def choice(self, seq: "Sequence[Any]") -> "Any":  # type: ignore[override]
        return seq[min(self.indice, len(seq) - 1)]


def _caso_de_pista(
    huecos: int, posicion: int, ultimo: int | None, tipo: str, mentir: bool
) -> dict:
    posibles: list[dict] = []
    for indice in (0, 1):
        pista = pistas.generar_pista(
            posicion,
            huecos,
            ultimo,
            tipo=tipo,
            mentir=mentir,
            rng=_RngFijo(indice),
        )
        como_dict = _pista_a_dict(pista)
        if como_dict not in posibles:
            posibles.append(como_dict)
    return {
        "huecos": huecos,
        "posicion": posicion,
        "ultimo": -1 if ultimo is None else ultimo,
        "tipo": tipo,
        "mentir": mentir,
        "posibles": posibles,
    }


def _pistas() -> list[dict]:
    casos = []
    for huecos in HUECOS_PROBADOS:
        combinaciones = itertools.product(
            range(1, huecos + 1),
            [None, *range(1, huecos + 1)],
            pistas.TIPOS_PISTA,
            (False, True),
        )
        for posicion, ultimo, tipo, mentir in combinaciones:
            if tipo == "relativa" and ultimo is None:
                continue
            casos.append(_caso_de_pista(huecos, posicion, ultimo, tipo, mentir))
    return casos


def _interseccion() -> list[dict]:
    grupos = [
        [],
        [[2, 4, 6, 8]],
        [[2, 4, 6, 8], [1, 2, 3, 4]],
        [[2, 4, 6, 8], [1, 3, 5, 7]],
        [[1, 2, 3, 4], [3, 4, 5, 6], [4, 5, 6, 7]],
        [[1, 2, 3], []],
    ]
    casos = []
    for grupo in grupos:
        lista = [pistas.Pista("", frozenset(c)) for c in grupo]
        casos.append(
            {"candidatos": grupo, "resultado": sorted(pistas.interseccion(lista))}
        )
    return casos


def _apuesta() -> list[dict]:
    guiones = [
        ["doblar"],
        ["doblar", "doblar", "doblar"],
        ["bono"],
        ["doblar", "bono", "doblar"],
        ["doblar", "perder"],
        ["doblar", "doblar", "retirarse"],
        ["bono", "bono", "perder"],
    ]
    casos = []
    for guion in guiones:
        apuesta = apuestas.Apuesta(ruleta.APUESTA_BASE)
        devueltos = []
        for paso in guion:
            if paso == "doblar":
                devueltos.append(apuesta.doblar())
            elif paso == "bono":
                devueltos.append(apuesta.sumar_bono(ruleta.BONO_MARCA_ACERTADA))
            elif paso == "perder":
                devueltos.append(apuesta.perder())
            else:
                devueltos.append(apuesta.retirarse())
        casos.append(
            {"guion": guion, "devueltos": devueltos, "en_juego": apuesta.en_juego}
        )
    return casos


def _farol() -> list[dict]:
    guiones: list[tuple[int, int, list[int]]] = [
        (3, 5, [2, 5, 7]),
        (1, 1, [1]),
        (2, 8, [8, 8]),
        (0, 4, []),
    ]
    casos = []
    for marcas, bala, huecos in guiones:
        marca = farol.Farol(marcas)
        aciertos = [marca.marcar(h, bala) for h in huecos]
        casos.append(
            {
                "marcas": marcas,
                "bala": bala,
                "huecos": huecos,
                "aciertos": aciertos,
                "restantes": marca.marcas_restantes,
                "puede_marcar": marca.puede_marcar(),
            }
        )
    return casos


def _resumen() -> list[dict]:
    combinaciones = [
        (0, 0, {}, 0),
        (0, 0, {}, 1),
        (0, 0, {}, 5),
        (1, 1, {}, 1),
        (1, 0, {}, 2),
        (3, 2, {}, 4),
        (0, 0, {"clic_metalico": 1}, 1),
        (0, 0, {"clic_metalico": 2, "tambor_caliente": 1}, 3),
        (2, 1, {"tambor_caliente": 1}, 2),
        (4, 3, {"clic_metalico": 2, "tambor_caliente": 2}, 7),
    ]
    casos = []
    for usados, acertados, evs, dias in combinaciones:
        bitacora = historial.Historial(
            faroles_usados=usados, faroles_acertados=acertados, eventos=dict(evs)
        )
        casos.append(
            {
                "faroles_usados": usados,
                "faroles_acertados": acertados,
                "eventos": evs,
                "dias": dias,
                "resultado": historial.resumen(bitacora, dias),
            }
        )
    return casos


def _ganadores() -> list[dict]:
    mesas: list[list[tuple[int, int, bool]]] = [
        [(9, 100, False), (18, 100, False)],
        [(18, 100, False), (9, 800, False)],
        [(9, 100, False), (9, 800, False)],
        [(9, 800, False), (9, 800, False)],
        [(0, 0, False), (0, 0, False)],
        [(27, 50, False), (9, 900, False), (27, 50, False)],
        [(3, 0, True), (2, 400, False)],
        [(4, 0, True), (2, 400, False)],
        [(4, 0, True), (3, 400, False)],
    ]
    casos = []
    for mesa in mesas:
        jugadores = []
        for indice, (disparos, puntos, murio) in enumerate(mesa):
            uno = jugador.Jugador(f"J{indice}", apuestas.Apuesta(100), farol.Farol(3))
            uno.disparos = disparos
            uno.murio = murio
            uno.puntos_finales = puntos
            jugadores.append(uno)
        vencedores = jugador.ganadores(jugadores)
        casos.append(
            {
                "mesa": [{"disparos": d, "puntos": p, "murio": m} for d, p, m in mesa],
                "dias": [uno.dias for uno in jugadores],
                "ganadores": [jugadores.index(v) for v in vencedores],
            }
        )
    return casos


def tabla() -> dict:
    return {
        "formato": FORMATO,
        "constantes": _constantes(),
        "mover": _mover(),
        "dias": _dias(),
        "pistas": _pistas(),
        "interseccion": _interseccion(),
        "apuesta": _apuesta(),
        "farol": _farol(),
        "resumen": _resumen(),
        "ganadores": _ganadores(),
    }


def escribir(ruta: Path | None = None) -> Path:
    destino = ruta or ruta_por_defecto()
    destino.write_text(
        json.dumps(tabla(), indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destino


if __name__ == "__main__":  # pragma: no cover
    escrito = escribir()
    print(f"Tabla de paridad escrita en {escrito}")
