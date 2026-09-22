"""Tabla de paridad entre la version de terminal y la de Godot.

Cada modulo de logica de `terminal/` tiene un hermano en `2d/` con la
misma mecanica escrita a mano en GDScript, y hasta ahora lo unico que lo
garantizaba era un comentario que decia "hermano de X.py". No bastaba:
escribiendo los tests de la semilla aparecieron dos divergencias en
`Pistas.gd` que llevaban ahi desde el principio (una pista mentirosa que
no mentia, y un candidato de mas en el lado derecho de una pista
relativa).

Este modulo genera una tabla de casos -- entradas y la salida que da la
version de Python -- que la version de Godot replica y compara en su
test headless (`2d/tests/test_paridad.gd`). Si las dos versiones dejan
de decir lo mismo, falla el CI en vez de descubrirse jugando.

Solo entran funciones puras que existen en las dos versiones. Quedan
fuera a proposito:

- El desempate de un duelo. Godot lo tiene en `Jugador.ganadores()`,
  pero en la terminal esta escrito dentro de `ruleta.resultado_duelo`,
  mezclado con el pintado, y no hay funcion pura que tabular. Entra en
  cuanto se saque de ahi.

- `ambiente.epilogo` y sus ocho finales, que son solo de la terminal.
- El orden en que cada version cuenta lo que pasa en un turno: son
  decisiones de interfaz, no reglas (ver la nota en motor.py).
- El generador de numeros aleatorios: Python usa Mersenne Twister y
  Godot PCG32, asi que una misma semilla no da la misma secuencia. Por
  eso aqui no se sortea nada: todos los casos fijan sus entradas.

Regenerar la tabla tras un cambio deliberado de reglas:

    python3 terminal/paridad.py
"""

import json
import random
from collections.abc import Sequence
from pathlib import Path
from typing import Any

try:
    from . import apuestas, estado, eventos, farol, historial, pistas, ruleta
except ImportError:  # pragma: no cover - ejecucion como script suelto
    import apuestas  # type: ignore[no-redef,import-not-found]
    import estado  # type: ignore[no-redef,import-not-found]
    import eventos  # type: ignore[no-redef,import-not-found]
    import farol  # type: ignore[no-redef,import-not-found]
    import historial  # type: ignore[no-redef,import-not-found]
    import pistas  # type: ignore[no-redef,import-not-found]
    import ruleta  # type: ignore[no-redef,import-not-found]

FORMATO = 1

# Tamaños de tambor que se recorren enteros. No hace falta probarlos
# todos: 6/8/10 son los tres presets de dificultad, y entre un par y un
# impar ya se cubren las dos formas de partir el tambor por la mitad.
HUECOS_PROBADOS = (6, 8, 10)

# La apuesta base, el bono del farol y los presets de dificultad viven
# hoy en ruleta.py (el modulo de interfaz) porque es quien los consume:
# los dos primeros para pintarlos y el tercero para argparse. Este
# modulo los lee de ahi en vez de copiarlos, que es justo el error que
# viene a cazar: una copia se desincroniza en silencio.


def ruta_por_defecto() -> Path:
    """Donde vive la tabla: dentro del proyecto de Godot, que es quien la
    lee en tiempo de test (`res://tests/paridad.json`)."""
    return Path(__file__).resolve().parent.parent / "2d" / "tests" / "paridad.json"


def _constantes() -> dict:
    """Los numeros y textos que las dos versiones declaran por separado.

    Es el caso mas tonto de divergencia y el mas facil de cometer: subir
    la probabilidad de eventos en un lado y olvidarse del otro no rompe
    nada, solo hace que los dos juegos dejen de ser el mismo juego.
    """
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
        "dificultades": ruleta.DIFICULTADES,
    }


def _mover() -> list[dict]:
    """Adonde va la bala desde cada hueco con cada patron."""
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
    """Cuantos dias son N disparos sobrevividos."""
    return [
        {"disparos": n, "resultado": estado.dias_sobrevividos(n)} for n in range(0, 13)
    ]


def _pista_a_dict(pista: "pistas.Pista") -> dict:
    return {"texto": pista.texto, "candidatos": sorted(pista.candidatos)}


class _RngFijo(random.Random):
    """Un generador que siempre elige la opcion `indice` de las que haya.

    La unica pista que sortea algo es la relativa mentirosa cuando la
    bala cayo justo en el ultimo disparo: elige un lado al azar de entre
    los que existen. Fijando ese sorteo se pueden anotar las dos
    respuestas posibles en vez de una sola.

    Hereda de random.Random en vez de ser una clase suelta con un
    `choice` para que encaje donde se pide un generador de verdad, que
    es lo unico que generar_pista acepta.
    """

    def __init__(self, indice: int) -> None:
        super().__init__()
        self.indice = indice

    # El `choice` de random.Random esta declarado sobre una Sequence
    # generica; aqui solo se usa con la lista de dos lados de una pista
    # relativa, asi que se anota con lo que de verdad recibe.
    def choice(self, seq: "Sequence[Any]") -> "Any":  # type: ignore[override]
        return seq[min(self.indice, len(seq) - 1)]


def _pistas() -> list[dict]:
    """Texto y candidatos de cada pista posible, veraz y mentirosa.

    `posibles` lleva todas las respuestas validas: casi siempre una, y
    dos en el caso de la relativa mentirosa con la bala en el ultimo
    disparo, que elige lado al azar. La version de Godot pasa el caso si
    da cualquiera de ellas.
    """
    casos = []
    for huecos in HUECOS_PROBADOS:
        for posicion in range(1, huecos + 1):
            for ultimo in [None, *range(1, huecos + 1)]:
                for tipo in pistas.TIPOS_PISTA:
                    if tipo == "relativa" and ultimo is None:
                        continue
                    for mentir in (False, True):
                        posibles = []
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
                        casos.append(
                            {
                                "huecos": huecos,
                                "posicion": posicion,
                                "ultimo": -1 if ultimo is None else ultimo,
                                "tipo": tipo,
                                "mentir": mentir,
                                "posibles": posibles,
                            }
                        )
    return casos


def _interseccion() -> list[dict]:
    """El cruce de varias pistas, incluido el cruce vacio."""
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
    """Como evoluciona lo que hay en juego con cada operacion."""
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
    """Aciertos y marcas restantes al gastar marcas seguidas."""
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
    """La frase narrativa del final, con todas sus concordancias.

    Es texto que las dos versiones construyen a mano trozo a trozo, con
    sus singulares y plurales: justo la clase de cosa que se desincroniza
    al retocar una palabra en un solo lado.
    """
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


def tabla() -> dict:
    """La tabla entera, tal como se escribe a disco."""
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
    }


def escribir(ruta: Path | None = None) -> Path:
    """Vuelca la tabla a disco, ordenada y con saltos de linea.

    Ordenada e indentada para que el diff de un cambio de reglas se lea:
    la gracia de tener la tabla versionada es ver en la revision que
    casos han cambiado de respuesta.
    """
    destino = ruta or ruta_por_defecto()
    destino.write_text(
        json.dumps(tabla(), indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destino


if __name__ == "__main__":  # pragma: no cover - utilidad de linea de comandos
    escrito = escribir()
    print(f"Tabla de paridad escrita en {escrito}")
