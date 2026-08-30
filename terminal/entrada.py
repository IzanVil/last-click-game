"""Lectura de teclas sueltas (sin Enter) para el selector del tambor.

En una terminal de verdad se puede leer tecla a tecla: eso permite
recorrer los huecos con las flechas y disparar con Enter, en vez de
teclear un numero. Es lo unico que necesita hablar con `termios` (Unix)
o `msvcrt` (Windows), asi que queda aislado aqui.

Los dos modulos de plataforma se importan en caliente y por nombre: uno
de los dos no existe nunca en la maquina donde corre el juego, y asi ni
el import ni el analisis de tipos dependen del sistema operativo. Si
ninguno esta disponible, o la entrada no es una terminal (un pipe, los
tests, CI), `modo_tecla_disponible` devuelve False y la interfaz se
queda con el metodo de siempre: escribir el numero y pulsar Enter.
"""

import importlib
import os
import sys
from collections.abc import Callable
from typing import Any

# Nombres canonicos que devuelve `leer_tecla`; cualquier otra tecla se
# devuelve tal cual (un caracter suelto, ya en minuscula).
IZQUIERDA = "izquierda"
DERECHA = "derecha"
ARRIBA = "arriba"
ABAJO = "abajo"
ENTER = "enter"
ESCAPE = "escape"

# Tercer byte de las secuencias de flecha en Unix (ESC [ X) y segundo
# caracter del codigo extendido de Windows.
_FLECHAS_UNIX = {"A": ARRIBA, "B": ABAJO, "C": DERECHA, "D": IZQUIERDA}
_FLECHAS_WINDOWS = {"H": ARRIBA, "P": ABAJO, "M": DERECHA, "K": IZQUIERDA}


def _modulo(nombre: str) -> Any | None:
    """Importa un modulo de plataforma, o None si no existe aqui."""
    try:
        return importlib.import_module(nombre)
    except ImportError:  # pragma: no cover - depende del sistema operativo
        return None


def _modulo_obligatorio(nombre: str) -> Any:
    """Como `_modulo`, pero para cuando ya se sabe que el modulo esta.

    Solo se llama desde las funciones de lectura, y a esas no se llega
    sin que `modo_tecla_disponible` haya dicho que si; si aun asi
    faltara, mejor un error claro que un `None` propagandose.
    """
    modulo = _modulo(nombre)
    if modulo is None:  # pragma: no cover - lo descarta modo_tecla_disponible
        raise RuntimeError(f"Este sistema no puede leer el teclado sin {nombre}.")
    return modulo


def _hay_entrada_interactiva() -> bool:
    """True si stdin es una terminal (y no un fichero, un pipe o un test)."""
    try:
        return bool(sys.stdin.isatty())
    except (AttributeError, ValueError):  # pragma: no cover - stdin exotico
        return False


def modo_tecla_disponible() -> bool:
    """Indica si se puede leer tecla a tecla en esta maquina y sesion."""
    if not _hay_entrada_interactiva():
        return False
    if os.name == "nt":
        return _modulo("msvcrt") is not None
    return _modulo("termios") is not None and _modulo("tty") is not None


def _leer_tecla_windows() -> str:
    """Lee una tecla con msvcrt (Windows)."""
    msvcrt = _modulo_obligatorio("msvcrt")
    caracter = msvcrt.getwch()
    if caracter in ("\x00", "\xe0"):  # prefijo de tecla extendida (flechas)
        return _FLECHAS_WINDOWS.get(msvcrt.getwch(), "")
    if caracter in ("\r", "\n"):
        return ENTER
    if caracter == "\x1b":
        return ESCAPE
    if caracter == "\x03":
        raise KeyboardInterrupt
    return caracter.lower()


def _leer_tecla_unix() -> str:
    """Lee una tecla en crudo con termios/tty (Linux y macOS)."""
    termios = _modulo_obligatorio("termios")
    tty = _modulo_obligatorio("tty")
    descriptor = sys.stdin.fileno()
    ajustes_previos = termios.tcgetattr(descriptor)
    try:
        tty.setraw(descriptor)
        caracter = sys.stdin.read(1)
        if caracter == "\x1b":
            # Puede ser un ESC suelto o el principio de una flecha
            # (ESC [ A..D). Los dos caracteres que faltan ya estan en el
            # buffer si es una flecha, asi que leerlos no bloquea.
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
    """Lee una tecla sin esperar a Enter.

    Devuelve uno de los nombres canonicos de arriba, el caracter pulsado
    en minuscula, o "" si fue una secuencia que no interesa. Ctrl+C se
    convierte en KeyboardInterrupt para que salga por el mismo sitio que
    en el resto del juego.
    """
    if os.name == "nt":
        return _leer_tecla_windows()
    return _leer_tecla_unix()


def seleccionar(
    huecos: int,
    pintar: Callable[[int], None],
    inicio: int = 1,
) -> int | None:
    """Recorre los huecos del tambor con las flechas y confirma con Enter.

    `pintar` dibuja la pantalla con un hueco resaltado; se le llama en
    cada movimiento. Ademas de las flechas se aceptan las teclas a/d
    (para quien prefiera el teclado de siempre) y los digitos 1-9, que
    saltan directos a ese hueco. Devuelve el hueco elegido, o None si el
    jugador se echa atras con Esc o Q.
    """
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
        elif tecla.isdigit() and 1 <= int(tecla) <= huecos:
            seleccion = int(tecla)
        else:
            continue
        pintar(seleccion)
