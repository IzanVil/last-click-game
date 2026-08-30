"""Efectos de terminal de "El Tambor del Juicio": pantalla, tiempo y sonido.

Este modulo no sabe nada del juego: solo ofrece las primitivas de
presentacion (limpiar, mover el cursor, escribir letra a letra, pitar,
repintar un bloque de lineas ya montado) que usa la interfaz en
ruleta.py. La logica pura (estado.py y companiia) no lo importa nunca.

Todo lo que consume tiempo o hace ruido pasa por `AJUSTES`, que la CLI
configura una sola vez al arrancar (--sin-animaciones / --sin-sonido).
Con las animaciones apagadas nada duerme ni parpadea, que es justo lo
que necesitan los tests y CI, donde no hay una terminal delante.
"""

import re
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

# Prefijo de las secuencias ANSI ("Control Sequence Introducer"): todo lo
# que mueve el cursor o borra pantalla empieza asi.
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

# Cada patron es la espera (en segundos) ANTES de cada pitido. El timbre
# de la terminal (BEL) no tiene tono que ajustar, asi que lo que
# distingue a un sonido de otro es el ritmo: cuantos pips suenan y como
# de separados. Un pip seco no se parece en nada a una rafaga de cuatro.
PATRONES_SONIDO: dict[str, tuple[float, ...]] = {
    "clic": (0.0,),
    "fallo": (0.0, 0.10),
    "impacto": (0.0, 0.05, 0.05, 0.30),
    "acierto": (0.0, 0.07, 0.07),
    "zumbido": (0.0, 0.16, 0.16, 0.16),
}

# Secuencia ANSI completa: se usa para que el tecleo letra a letra no
# gaste tiempo "escribiendo" codigos de color, que son invisibles.
_SECUENCIA_ANSI = re.compile(r"\033\[[0-9;?]*[A-Za-z]")


@dataclass
class Ajustes:
    """Interruptores globales de presentacion (ver `configurar`)."""

    animaciones: bool = True
    sonido: bool = True


AJUSTES = Ajustes()


def hay_terminal() -> bool:
    """Indica si la salida es una terminal de verdad y no un fichero o pipe.

    Cuando el juego se ejecuta con la salida redirigida (o desde los
    tests) no hay nadie mirando: ni el timbre ni el teclado en crudo
    tienen sentido ahi.
    """
    try:
        return bool(sys.stdout.isatty())
    except (AttributeError, ValueError):  # pragma: no cover - stdout exotico
        return False


def configurar(animaciones: bool = True, sonido: bool = True) -> None:
    """Fija los interruptores globales. La CLI la llama una sola vez.

    El sonido se apaga tambien, aunque se pida, si no hay una terminal
    de verdad detras: un BEL en un fichero de log solo ensucia.
    """
    AJUSTES.animaciones = animaciones
    AJUSTES.sonido = sonido and hay_terminal()


def _volcar(texto: str) -> None:
    """Escribe sin salto de linea y vacia el buffer, para que se vea ya."""
    sys.stdout.write(texto)
    sys.stdout.flush()


def limpiar(duro: bool = False) -> None:
    """Deja la pantalla en blanco con el cursor arriba del todo.

    Por defecto se usa "ir arriba + borrar hacia abajo", que repinta sin
    el parpadeo (ni el proceso hijo) de un `clear`/`cls` del sistema:
    esta funcion se llama en cada fotograma, asi que importa. Con
    `duro=True` se borra ademas el historial de scroll, lo que solo hace
    falta al arrancar y al terminar.

    Sin animaciones no se borra nada: la partida se convierte en un
    registro que va bajando, que es lo que se quiere al redirigir la
    salida a un fichero, en CI o con un lector de pantalla delante.
    """
    if not AJUSTES.animaciones:
        return
    _volcar(f"{CSI}2J{CSI}3J{CSI}H" if duro else f"{CSI}H{CSI}J")


def ir_a(fila: int, columna: int = 1) -> None:
    """Coloca el cursor en una posicion absoluta de la pantalla."""
    _volcar(f"{CSI}{fila};{columna}H")


def cursor(visible: bool) -> None:
    """Muestra u oculta el cursor, que molesta durante las animaciones.

    Sin animaciones no hay nada que esconder (ni pantalla que tocar):
    no se emite ningun codigo.
    """
    if not AJUSTES.animaciones:
        return
    _volcar(f"{CSI}?25h" if visible else f"{CSI}?25l")


def pausa(segundos: float) -> None:
    """Espera, salvo que las animaciones esten apagadas."""
    if AJUSTES.animaciones:
        time.sleep(segundos)


def _partes(texto: str) -> Iterable[tuple[str, bool]]:
    """Trocea `texto` en (trozo, es_secuencia_ansi) conservando el orden."""
    posicion = 0
    for coincidencia in _SECUENCIA_ANSI.finditer(texto):
        yield texto[posicion : coincidencia.start()], False
        yield coincidencia.group(), True
        posicion = coincidencia.end()
    yield texto[posicion:], False


def escribir(texto: str, retardo: float = RETARDO_TECLEO, salto: bool = True) -> None:
    """Imprime `texto` letra a letra, como una teletipo imprimiendo.

    Los codigos de color se vuelcan de golpe (son invisibles: teclearlos
    solo seria tiempo muerto) y los espacios no esperan, para que la
    cadencia se parezca a la de una maquina de escribir de verdad. Sin
    animaciones sale por `print`, de una vez: es el camino que siguen el
    resto de mensajes del juego cuando no hay pantalla que animar.
    """
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
    """Hace sonar el timbre de la terminal con el ritmo de `patron`."""
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
    """Pinta un bloque de lineas, opcionalmente pisando el anterior.

    Con `subir` > 0 el cursor retrocede esas lineas antes de pintar, de
    modo que el bloque nuevo cae justo encima del viejo sin tocar el
    resto de la pantalla. Cada linea se borra hasta el final para que no
    queden restos de un fotograma mas ancho. Sin animaciones se imprime
    tal cual, sin mover el cursor: no hay pantalla que repintar.
    """
    if not AJUSTES.animaciones:
        print(fotograma)
        return
    if subir:
        _volcar(f"{CSI}{subir}A")
    for linea in fotograma.split("\n"):
        _volcar(f"{linea}{CSI}K\n")


def ancho_visible(texto: str) -> int:
    """Longitud de `texto` en pantalla, sin contar los codigos de color.

    Es lo que hace falta para alinear un marco: los codigos ANSI ocupan
    caracteres en la cadena pero ninguna columna en la terminal.
    """
    return len(_SECUENCIA_ANSI.sub("", texto))


def alto_de(fotograma: str) -> int:
    """Numero de lineas que ocupa un fotograma al pintarlo."""
    return fotograma.count("\n") + 1


def repintar(
    fotogramas: Sequence[str],
    retardo: float = RETARDO_FOTOGRAMA,
    factor: float = 1.0,
) -> None:
    """Anima una secuencia de fotogramas del mismo alto, en el sitio.

    Se da por hecho que en pantalla, justo encima del cursor, ya hay un
    bloque del mismo alto (el que acaba de pintar la escena): el primer
    fotograma lo pisa, igual que cada fotograma pisa al anterior. Al
    terminar queda pintado el ultimo, asi que conviene que sea el estado
    en reposo.

    `factor` multiplica la espera tras cada fotograma: por debajo de 1
    el ritmo acelera (el latido del tambor cuando la bala esta cerca) y
    por encima frena (el tambor girando hasta pararse). Sin animaciones
    no hace nada: es un efecto de transito, y la escena de verdad ya
    esta pintada debajo.
    """
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
    """Planta un cartel a pantalla completa y lo deja unos segundos.

    A diferencia de `repintar`, un banner tambien se imprime con las
    animaciones apagadas (sin la espera): anuncia algo que ha pasado en
    la partida, no es un adorno.
    """
    limpiar()
    print()
    print()
    for linea in lineas:
        print(f"{color}   {linea}{RESET}" if color else f"   {linea}")
    print()
    pausa(segundos)
