import io
import os
import re
import shutil
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TextIO

CSI = "\033["
BEL = "\a"

ROJO = "\033[91m"
VERDE = "\033[92m"
AMARILLO = "\033[93m"
CELESTE = "\033[96m"
GRIS = "\033[90m"
NEGRITA = "\033[1m"
INVERSO = "\033[7m"
RESET = "\033[0m"

RETARDO_TECLEO = 0.018
RETARDO_FOTOGRAMA = 0.06

PATRONES_SONIDO: dict[str, tuple[float, ...]] = {
    "clic": (0.0,),
    "fallo": (0.0, 0.10),
    "impacto": (0.0, 0.05, 0.05, 0.30),
    "acierto": (0.0, 0.07, 0.07),
    "zumbido": (0.0, 0.16, 0.16, 0.16),
}

_SECUENCIA_ANSI = re.compile(r"\033\[[0-9;?]*[A-Za-z]")

_SECUENCIA_COLOR = re.compile(r"\033\[[0-9;]*m")


@dataclass
class Ajustes:
    animaciones: bool = True
    sonido: bool = True


AJUSTES = Ajustes()


class _SalidaSinColor(io.TextIOBase):
    def __init__(self, destino: TextIO) -> None:
        self._destino = destino

    @property
    def destino(self) -> TextIO:
        return self._destino

    def write(self, texto: str) -> int:
        self._destino.write(_SECUENCIA_COLOR.sub("", texto))
        return len(texto)

    def flush(self) -> None:
        self._destino.flush()

    def isatty(self) -> bool:
        return self._destino.isatty()

    def fileno(self) -> int:
        return self._destino.fileno()

    def writable(self) -> bool:
        return True


def asegurar_utf8(salida: TextIO | None = None) -> None:
    destino = sys.stdout if salida is None else salida
    reconfigurar = getattr(destino, "reconfigure", None)
    if reconfigurar is None:
        return
    try:
        reconfigurar(encoding="utf-8")
    except (ValueError, OSError, LookupError):  # pragma: no cover
        try:
            reconfigurar(errors="replace")
        except (ValueError, OSError, LookupError):
            pass


def color_activo(sin_color: bool = False) -> bool:
    if sin_color or os.environ.get("NO_COLOR"):
        return False
    return hay_terminal()


def filtrar_color(activo: bool) -> None:
    salida = sys.stdout
    if activo and not isinstance(salida, _SalidaSinColor):
        sys.stdout = _SalidaSinColor(salida)
    elif not activo and isinstance(salida, _SalidaSinColor):
        sys.stdout = salida.destino


def ancho_terminal() -> int:
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def hay_terminal() -> bool:
    try:
        return bool(sys.stdout.isatty())
    except (AttributeError, ValueError):  # pragma: no cover
        return False


def configurar(animaciones: bool = True, sonido: bool = True) -> None:
    AJUSTES.animaciones = animaciones
    AJUSTES.sonido = sonido and hay_terminal()


def _volcar(texto: str) -> None:
    sys.stdout.write(texto)
    sys.stdout.flush()


def limpiar(duro: bool = False) -> None:
    if not AJUSTES.animaciones:
        return
    _volcar(f"{CSI}2J{CSI}3J{CSI}H" if duro else f"{CSI}H{CSI}J")


def ir_a(fila: int, columna: int = 1) -> None:
    _volcar(f"{CSI}{fila};{columna}H")


def cursor(visible: bool) -> None:
    if not AJUSTES.animaciones:
        return
    _volcar(f"{CSI}?25h" if visible else f"{CSI}?25l")


def pausa(segundos: float) -> None:
    if AJUSTES.animaciones:
        time.sleep(segundos)


def _partes(texto: str) -> Iterable[tuple[str, bool]]:
    posicion = 0
    for coincidencia in _SECUENCIA_ANSI.finditer(texto):
        yield texto[posicion : coincidencia.start()], False
        yield coincidencia.group(), True
        posicion = coincidencia.end()
    yield texto[posicion:], False


def escribir(texto: str, retardo: float = RETARDO_TECLEO, salto: bool = True) -> None:
    if not AJUSTES.animaciones:
        if salto:
            print(texto)
        else:
            _volcar(texto)
        return

    for trozo, es_ansi in _partes(texto):
        if es_ansi:
            _volcar(trozo)
            continue
        for caracter in trozo:
            _volcar(caracter)
            if caracter != " ":
                time.sleep(retardo)
    if salto:
        _volcar("\n")


def beep(patron: str = "clic") -> None:
    if not AJUSTES.sonido:
        return
    esperas = PATRONES_SONIDO.get(patron)
    if esperas is None:
        raise ValueError(f"Patron de sonido desconocido: {patron}")
    for espera in esperas:
        if espera:
            pausa(espera)
        _volcar(BEL)


def pintar_bloque(fotograma: str, subir: int = 0) -> None:
    if not AJUSTES.animaciones:
        print(fotograma)
        return
    if subir:
        _volcar(f"{CSI}{subir}A")
    for linea in fotograma.split("\n"):
        _volcar(f"{linea}{CSI}K\n")


def ancho_visible(texto: str) -> int:
    return len(_SECUENCIA_ANSI.sub("", texto))


def alto_de(fotograma: str) -> int:
    return fotograma.count("\n") + 1


def repintar(
    fotogramas: Sequence[str],
    retardo: float = RETARDO_FOTOGRAMA,
    factor: float = 1.0,
) -> None:
    if not AJUSTES.animaciones or not fotogramas:
        return

    cursor(False)
    try:
        espera = retardo
        for indice, fotograma in enumerate(fotogramas):
            anterior = fotogramas[indice - 1] if indice else fotogramas[0]
            pintar_bloque(fotograma, alto_de(anterior))
            time.sleep(espera)
            espera *= factor
    finally:
        cursor(True)


def banner(lineas: Sequence[str], color: str = "", segundos: float = 2.0) -> None:
    limpiar()
    print()
    print()
    for linea in lineas:
        print(f"{color}   {linea}{RESET}" if color else f"   {linea}")
    print()
    pausa(segundos)
