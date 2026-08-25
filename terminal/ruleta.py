import os
import random
import sys
import time

HUECOS = 10
RONDAS = 8

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


def dibujar_tambor(marcadas: set[int]) -> None:
    """Imprime el tambor ASCII marcando los huecos ya probados."""
    marco = "┌" + "─┬" * (HUECOS - 1) + "─┐"
    celdas = []
    etiquetas = []
    for i in range(1, HUECOS + 1):
        if i in marcadas:
            celdas.append(_c("·", GRIS))
        else:
            celdas.append(_c("0", CELESTE))
        etiquetas.append(str(i))
    print("   " + _c(marco, NEGRITA))
    print("   " + "   ".join(celdas))
    print("   " + _c("└" + "─┴" * (HUECOS - 1) + "─┘", NEGRITA))
    print("   " + "  ".join(etiquetas))


def cabecera(ronda: int, balas: int) -> None:
    """Imprime el marco superior con la ronda actual, balas y huecos vacios."""
    vacios = HUECOS - balas
    doble = NEGRITA + CELESTE
    print(_c("╔" + "═" * 44 + "╗", doble))
    print(_c("║", doble) + "            RULETA RUSA              " + _c("║", doble))
    print(
        _c("║", doble) + f"   Ronda {_c(f'{ronda:^2}', AMARILLO)}/{RONDAS}"
        f"  ·  Balas {_c(f'{balas:^2}', ROJO)}"
        f"  ·  Vacios {_c(f'{vacios:^2}', VERDE)}  " + _c("║", doble)
    )
    print(_c("╚" + "═" * 44 + "╝", doble))


def colocar_balas(cantidad: int) -> set[int]:
    """Genera un conjunto de posiciones unicas con balas en el tambor."""
    posiciones = set()
    while len(posiciones) < cantidad:
        posiciones.add(random.randint(1, HUECOS))
    return posiciones


def elegir_posicion(marcadas: set[int]) -> int:
    """Pide al jugador una posicion valida y aun no probada del tambor."""
    while True:
        entrada = input(_c(f"   Elige una posicion (1-{HUECOS}): ", NEGRITA)).strip()
        try:
            posicion = int(entrada)
        except ValueError:
            print(_c("   Eso no parece un numero.", ROJO))
            continue
        if posicion < 1 or posicion > HUECOS:
            print(_c("   Ese numero no esta en el tambor.", ROJO))
            continue
        if posicion in marcadas:
            print(_c("   Ya has probado esa posicion.", AMARILLO))
            continue
        return posicion


def escena(ronda: int, balas: int, marcadas: set[int]) -> None:
    """Limpia la pantalla y dibuja la cabecera y el tambor de la ronda."""
    limpiar()
    cabecera(ronda, balas)
    print()
    print(_c("   La bala descansa en un hueco. Tu huella deja marcas.", GRIS))
    dibujar_tambor(marcadas)
    print()


def fracaso(ronda: int) -> None:
    """Muestra la pantalla de derrota (BOOM) para la ronda indicada."""
    limpiar()
    print(_c("\n      ▓▓▓   B O O M   ▓▓▓\n", NEGRITA + ROJO))
    print(_c("   La bala ha encontrado tu numero.", ROJO))
    print(_c(f"   Caiste en la ronda {ronda} de {RONDAS}.\n", AMARILLO))
    time.sleep(2)


def victoria() -> None:
    """Muestra la pantalla de victoria tras superar todas las rondas."""
    limpiar()
    print(_c("\n    ✦  HAS SOBREVIVIDO  ✦\n", NEGRITA + VERDE))
    print(_c(f"   Superaste las {RONDAS} rondas del tambor.", CELESTE))
    print(_c("   No eres de este mundo. Eres una leyenda.\n", VERDE))
    time.sleep(2)


def jugar() -> None:
    """Ejecuta el bucle principal del juego hasta que el jugador se retira."""
    while True:
        ronda = 1

        while ronda <= RONDAS:
            balas = ronda
            posiciones_bala = colocar_balas(balas)
            marcadas = set()

            escena(ronda, balas, marcadas)
            elegida = elegir_posicion(marcadas)

            if elegida in posiciones_bala:
                fracaso(ronda)
                input(_c("   Pulsa Enter para volver a empezar...", NEGRITA))
                break

            print(
                _c(
                    f"   Click. Cartucho vacio. Avanzas a la ronda {ronda + 1}.",
                    VERDE,
                )
            )
            time.sleep(1.5)
            ronda += 1

        if ronda > RONDAS:
            victoria()
            otra = input(_c("   Volver a jugar? (s/n): ", NEGRITA)).strip().lower()
            if otra not in ("s", "si", "y", "yes"):
                print(_c("   Hasta la proxima. El tambor siempre espera.", AMARILLO))
                break


if __name__ == "__main__":
    try:
        jugar()
    except KeyboardInterrupt:
        print()
        print(_c("   Hasta la proxima. El tambor siempre espera.", AMARILLO))
