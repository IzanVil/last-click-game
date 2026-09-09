import argparse
import os
import random
import shutil
import sys
import time
from importlib.metadata import PackageNotFoundError, version

HUECOS = 10
RONDAS = 8

# Ancho minimo (en columnas visibles) del interior del marco de cabecera().
# Es un minimo, no un maximo: si los datos de la ronda no caben, el marco
# se ensancha en vez de desbordarse.
ANCHO_MARCO = 44

ROJO = "\033[91m"
VERDE = "\033[92m"
AMARILLO = "\033[93m"
CELESTE = "\033[96m"
GRIS = "\033[90m"
NEGRITA = "\033[1m"
RESET = "\033[0m"

if os.name == "nt":
    # Habilita el procesamiento VT100 (codigos ANSI) en cmd.exe moderno:
    # es un efecto secundario documentado de esta llamada "vacia", sin
    # necesitar ninguna dependencia extra (colorama, etc.). Sin esto, en
    # un cmd.exe "clasico" los codigos de color de abajo se verian
    # literales en pantalla en vez de colorear.
    os.system("")


def _color_activo() -> bool:
    """Decide si conviene emitir codigos ANSI: no si se pidio
    explicitamente NO_COLOR (https://no-color.org) ni si la salida no es
    una terminal interactiva (pipe, log, CI...).
    """
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _c(texto: str, color: str) -> str:
    """Envuelve `texto` en `color` + RESET, o lo devuelve tal cual si el
    color esta desactivado. Centraliza el criterio de _color_activo() en
    un unico sitio en vez de repetirlo (o no) en cada print suelto.
    """
    if not _color_activo():
        return texto
    return f"{color}{texto}{RESET}"


def limpiar() -> None:
    """Limpia la pantalla de la terminal segun el sistema operativo."""
    os.system("cls" if os.name == "nt" else "clear")


def _ancho_terminal() -> int:
    """Columnas disponibles en la terminal, con un fallback razonable si
    no se pueden averiguar (salida redirigida, CI...).
    """
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def dibujar_tambor(huecos: int = HUECOS) -> None:
    """Imprime el tambor ASCII con sus huecos numerados.

    Todas las columnas miden lo mismo (el ancho del numero mas largo, mas
    un margen), asi que el numero de cada hueco cae siempre justo debajo
    de su celda: antes las celdas se separaban con 3 espacios y las
    etiquetas con 2, de modo que ya con los 10 huecos por defecto la
    fila de numeros iba corriendose respecto al tambor. Si el tambor no
    cabe a lo ancho de la terminal se parte en varias filas en vez de
    desbordarse (p. ej. --huecos 40).
    """
    ancho_celda = len(str(huecos)) + 2
    # +1 por el separador (┬) que va entre celda y celda; el margen de 3
    # de la izquierda y el borde final (┐) se descuentan aparte.
    por_fila = max(1, (_ancho_terminal() - 4) // (ancho_celda + 1))

    for inicio in range(0, huecos, por_fila):
        posiciones = range(inicio + 1, min(inicio + por_fila, huecos) + 1)
        segmentos = ["─" * ancho_celda] * len(posiciones)
        # Se colorea la fila entera y no celda a celda: asi el .rstrip()
        # (que quita el relleno sobrante de la ultima celda) actua sobre
        # espacios de verdad y no sobre el codigo RESET que iria detras.
        celdas = " ".join("0".center(ancho_celda) for _ in posiciones).rstrip()
        etiquetas = " ".join(str(i).center(ancho_celda) for i in posiciones).rstrip()

        print("   " + _c("┌" + "┬".join(segmentos) + "┐", NEGRITA))
        print("    " + _c(celdas, CELESTE))
        print("   " + _c("└" + "┴".join(segmentos) + "┘", NEGRITA))
        print("    " + etiquetas)


def cabecera(
    ronda: int, balas: int, huecos: int = HUECOS, rondas: int = RONDAS
) -> None:
    """Imprime el marco superior con la ronda actual, balas y huecos vacios.

    El relleno de cada fila se calcula sobre el texto *sin* color: len()
    de una cadena ya coloreada cuenta tambien los codigos ANSI, que no
    ocupan ninguna columna en pantalla, y usarlo descuadraba el cierre
    del marco.
    """
    vacios = huecos - balas
    doble = NEGRITA + CELESTE

    datos_plano = f"   Ronda {ronda}/{rondas}  ·  Balas {balas}  ·  Vacios {vacios}"
    datos_color = (
        f"   Ronda {_c(str(ronda), AMARILLO)}/{rondas}"
        f"  ·  Balas {_c(str(balas), ROJO)}"
        f"  ·  Vacios {_c(str(vacios), VERDE)}"
    )
    # Un tambor grande (--huecos 200) hace la linea de datos mas larga que
    # ANCHO_MARCO: en ese caso manda el contenido, +3 para dejar el mismo
    # margen a la derecha que el que lleva a la izquierda.
    ancho = max(ANCHO_MARCO, len(datos_plano) + 3)

    print(_c("╔" + "═" * ancho + "╗", doble))
    print(_c("║", doble) + "RULETA RUSA".center(ancho) + _c("║", doble))
    print(
        _c("║", doble) + datos_color + " " * (ancho - len(datos_plano)) + _c("║", doble)
    )
    print(_c("╚" + "═" * ancho + "╝", doble))


def colocar_balas(cantidad: int, huecos: int = HUECOS) -> set[int]:
    """Genera un conjunto de posiciones unicas con balas en el tambor.

    Si `cantidad` superase a `huecos`, random.sample lanza ValueError en
    vez de colgarse: con el enfoque anterior (randint en bucle hasta
    juntar `cantidad` posiciones distintas) esa situacion nunca converge.
    jugar_partida() ya valida rondas <= huecos (via _validar_dificultad)
    antes de la primera ronda, asi que esto no deberia llegar a pasar en
    una partida real; queda como red de seguridad de todas formas.
    """
    return set(random.sample(range(1, huecos + 1), cantidad))


def elegir_posicion(huecos: int = HUECOS) -> int:
    """Pide al jugador una posicion valida del tambor."""
    while True:
        entrada = input(_c(f"   Elige una posicion (1-{huecos}): ", NEGRITA)).strip()
        try:
            posicion = int(entrada)
        except ValueError:
            print(_c("   Eso no parece un numero.", ROJO))
            continue
        if posicion < 1 or posicion > huecos:
            print(_c("   Ese numero no esta en el tambor.", ROJO))
            continue
        return posicion


def escena(ronda: int, balas: int, huecos: int = HUECOS, rondas: int = RONDAS) -> None:
    """Limpia la pantalla y dibuja la cabecera y el tambor de la ronda.

    El aviso dice cuantas balas hay de verdad en esta ronda: el texto
    anterior ("La bala descansa en un hueco. Tu huella deja marcas.")
    hablaba de una sola bala cuando en la ronda N hay N, y prometia unas
    marcas de posiciones ya probadas que se eliminaron del juego.
    """
    limpiar()
    cabecera(ronda, balas, huecos, rondas)
    print()
    if balas == 1:
        aviso = "Hay 1 bala escondida en el tambor."
    else:
        aviso = f"Hay {balas} balas escondidas en el tambor."
    print(_c(f"   {aviso} Elige donde apretar el gatillo.", GRIS))
    dibujar_tambor(huecos)
    print()


def fracaso(ronda: int, rondas: int = RONDAS) -> None:
    """Muestra la pantalla de derrota (BOOM) para la ronda indicada."""
    limpiar()
    print(_c("\n      ▓▓▓   B O O M   ▓▓▓\n", NEGRITA + ROJO))
    print(_c("   La bala ha encontrado tu numero.", ROJO))
    print(_c(f"   Caiste en la ronda {ronda} de {rondas}.\n", AMARILLO))
    time.sleep(2)


def victoria(rondas: int = RONDAS) -> None:
    """Muestra la pantalla de victoria tras superar todas las rondas."""
    limpiar()
    print(_c("\n    ✦  HAS SOBREVIVIDO  ✦\n", NEGRITA + VERDE))
    print(_c(f"   Superaste las {rondas} rondas del tambor.", CELESTE))
    print(_c("   No eres de este mundo. Eres una leyenda.\n", VERDE))
    time.sleep(2)


def _validar_dificultad(huecos: int, rondas: int) -> None:
    """Comprueba que `huecos`/`rondas` son una combinacion jugable.

    Lanza ValueError con un mensaje claro si no lo son (mismo tipo de
    excepcion que ya lanza colocar_balas() para un mal uso similar, por
    consistencia). La usan tanto _parsear_args() (la CLI, que la
    traduce a un error de argparse con exit code 2) como jugar_partida()
    (para que llamar a la funcion directamente, sin pasar por la CLI,
    tambien falle alto y claro en vez de reventar con un ValueError
    mucho menos informativo de colocar_balas() a mitad de partida).
    """
    if huecos < 1:
        raise ValueError(f"huecos debe ser al menos 1 (recibido: {huecos}).")
    if rondas < 1:
        raise ValueError(f"rondas debe ser al menos 1 (recibido: {rondas}).")
    if rondas > huecos:
        raise ValueError(
            f"rondas ({rondas}) no puede ser mayor que huecos ({huecos}): "
            "la ultima ronda necesitaria mas balas de las que caben en el "
            "tambor."
        )


def jugar_partida(huecos: int = HUECOS, rondas: int = RONDAS) -> bool:
    """Juega una partida completa, ronda a ronda, hasta que el jugador
    muere o sobrevive las `rondas`. Devuelve True si sobrevive
    (victoria), False si muere en el camino (derrota) -- no decide que
    hacer con ese resultado (pantalla de victoria, preguntar si se
    quiere repetir...), de eso se encarga jugar().
    """
    _validar_dificultad(huecos, rondas)
    for ronda in range(1, rondas + 1):
        balas = ronda
        posiciones_bala = colocar_balas(balas, huecos)

        escena(ronda, balas, huecos, rondas)
        elegida = elegir_posicion(huecos)

        if elegida in posiciones_bala:
            fracaso(ronda, rondas)
            return False

        if ronda < rondas:
            print(
                _c(
                    f"   Click. Cartucho vacio. Avanzas a la ronda {ronda + 1}.",
                    VERDE,
                )
            )
            time.sleep(1.5)

    return True


def _quiere_otra_partida() -> bool:
    """Pregunta si se juega otra partida. Devuelve True solo ante un si
    explicito: cualquier otra cosa (incluido Enter a secas) se toma como
    "no", que es la respuesta segura para una pregunta de salida.
    """
    respuesta = input(_c("   Otra partida? (s/n): ", NEGRITA)).strip().lower()
    return respuesta in ("s", "si", "y", "yes")


def jugar(huecos: int = HUECOS, rondas: int = RONDAS) -> None:
    """Ejecuta el bucle principal del juego hasta que el jugador se retira.

    La pregunta de "otra partida?" se hace tanto al ganar como al perder.
    Antes solo se preguntaba al ganar: perder reiniciaba directamente el
    bucle, asi que la unica forma de salir del juego tras una derrota era
    matar el proceso con Ctrl+C.
    """
    while True:
        gano = jugar_partida(huecos, rondas)

        if gano:
            victoria(rondas)

        if not _quiere_otra_partida():
            print(_c("   Hasta la proxima. El tambor siempre espera.", AMARILLO))
            break


def _version_texto() -> str:
    """Version del paquete instalado (la que declara pyproject.toml), o
    un aviso claro si se ejecuta el script directamente sin instalar (no
    hay metadata de paquete que leer en ese caso: PackageNotFoundError).
    """
    try:
        return version("russian-roulette-2d")
    except PackageNotFoundError:
        return "sin instalar (ejecutado directamente)"


def _parsear_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Define y valida (via _validar_dificultad) las opciones de la CLI.

    Separado de main() para poder testearlo pasandole `argv` a mano, sin
    tocar el sys.argv real del proceso.
    """
    parser = argparse.ArgumentParser(
        prog="ruleta",
        description=(
            "Ruleta rusa de ficcion en la terminal: cada ronda anade una "
            "bala mas al tambor."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_texto()}",
    )
    parser.add_argument(
        "--huecos",
        type=int,
        default=HUECOS,
        help=f"Huecos del tambor (por defecto: {HUECOS}).",
    )
    parser.add_argument(
        "--rondas",
        type=int,
        default=RONDAS,
        help=f"Numero de rondas de la partida (por defecto: {RONDAS}).",
    )
    args = parser.parse_args(argv)

    try:
        _validar_dificultad(args.huecos, args.rondas)
    except ValueError as exc:
        # parser.error() imprime "ruleta: error: ..." + uso y termina con
        # exit code 2, igual que cualquier otro argumento invalido de
        # argparse (--huecos abc, etc.) -- mismo idioma de error para
        # todos los fallos de la CLI, en vez de un ValueError suelto.
        parser.error(str(exc))

    return args


def main(argv: list[str] | None = None) -> None:
    """Punto de entrada real del juego (usado por `run.sh`/`run.bat` via
    `__main__` y por el comando `ruleta` instalable via pyproject.toml):
    envuelve jugar() para que Ctrl+C siempre salga con el mensaje de
    despedida en vez de un traceback, sin importar por cual de las dos
    vias se haya lanzado. `argv=None` hace que argparse lea sys.argv
    real (comportamiento normal); se le puede pasar una lista para
    lanzar el juego con otros parametros sin pasar por la terminal.
    """
    args = _parsear_args(argv)
    try:
        jugar(args.huecos, args.rondas)
    except (KeyboardInterrupt, EOFError):
        # EOFError ademas de KeyboardInterrupt: el juego se apoya en
        # input(), que lo lanza cuando ya no queda entrada que leer
        # (Ctrl+D, o `echo | ruleta` / cualquier stdin redirigido y
        # agotado). Sin capturarlo, esos casos terminaban escupiendo un
        # traceback de EOFError en vez de la despedida.
        print()
        print(_c("   Hasta la proxima. El tambor siempre espera.", AMARILLO))


if __name__ == "__main__":
    main()
