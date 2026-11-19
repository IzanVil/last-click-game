import importlib
import os
import sys
from collections.abc import Callable
from typing import Any

IZQUIERDA = "izquierda"
DERECHA = "derecha"
ARRIBA = "arriba"
ABAJO = "abajo"
ENTER = "enter"
ESCAPE = "escape"

_FLECHAS_UNIX = {"A": ARRIBA, "B": ABAJO, "C": DERECHA, "D": IZQUIERDA}
_FLECHAS_WINDOWS = {"H": ARRIBA, "P": ABAJO, "M": DERECHA, "K": IZQUIERDA}


def _modulo(nombre: str) -> Any | None:
    try:
        return importlib.import_module(nombre)
    except ImportError:  # pragma: no cover
        return None


def _modulo_obligatorio(nombre: str) -> Any:
    modulo = _modulo(nombre)
    if modulo is None:  # pragma: no cover
        raise RuntimeError(f"Este sistema no puede leer el teclado sin {nombre}.")
    return modulo


def _hay_entrada_interactiva() -> bool:
    try:
        return bool(sys.stdin.isatty())
    except (AttributeError, ValueError):  # pragma: no cover
        return False


def modo_tecla_disponible() -> bool:
    if not _hay_entrada_interactiva():
        return False
    if os.name == "nt":
        return _modulo("msvcrt") is not None
    return _modulo("termios") is not None and _modulo("tty") is not None


def _leer_tecla_windows() -> str:
    msvcrt = _modulo_obligatorio("msvcrt")
    caracter = msvcrt.getwch()
    if caracter in ("\x00", "\xe0"):
        return _FLECHAS_WINDOWS.get(msvcrt.getwch(), "")
    if caracter in ("\r", "\n"):
        return ENTER
    if caracter == "\x1b":
        return ESCAPE
    if caracter == "\x03":
        raise KeyboardInterrupt
    return caracter.lower()


def _leer_tecla_unix() -> str:
    termios = _modulo_obligatorio("termios")
    tty = _modulo_obligatorio("tty")
    descriptor = sys.stdin.fileno()
    ajustes_previos = termios.tcgetattr(descriptor)
    try:
        tty.setraw(descriptor)
        caracter = sys.stdin.read(1)
        if caracter == "\x1b":
            siguiente = sys.stdin.read(1)
            if siguiente != "[":
                return ESCAPE
            return _FLECHAS_UNIX.get(sys.stdin.read(1), "")
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, ajustes_previos)

    if caracter in ("\r", "\n"):
        return ENTER
    if caracter == "\x03":
        raise KeyboardInterrupt
    return caracter.lower()


def leer_tecla() -> str:
    if os.name == "nt":
        return _leer_tecla_windows()
    return _leer_tecla_unix()


def seleccionar(
    huecos: int,
    pintar: Callable[[int], None],
    inicio: int = 1,
) -> int | None:
    seleccion = min(max(inicio, 1), huecos)
    pintar(seleccion)

    while True:
        tecla = leer_tecla()
        if tecla in (IZQUIERDA, ARRIBA, "a"):
            seleccion = huecos if seleccion == 1 else seleccion - 1
        elif tecla in (DERECHA, ABAJO, "d"):
            seleccion = 1 if seleccion == huecos else seleccion + 1
        elif tecla == ENTER:
            return seleccion
        elif tecla in (ESCAPE, "q"):
            return None
        elif tecla.isdecimal() and 1 <= int(tecla) <= huecos:
            seleccion = int(tecla)
        else:
            continue
        pintar(seleccion)
