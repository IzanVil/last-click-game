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


def dibujar_tambor() -> None:
    """Imprime el tambor ASCII con sus huecos numerados."""
    marco = "┌" + "─┬" * (HUECOS - 1) + "─┐"
    celdas = []
    etiquetas = []
    for i in range(1, HUECOS + 1):
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
    """Genera un conjunto de posiciones unicas con balas en el tambor.

    Si `cantidad` superase a HUECOS, random.sample lanza ValueError en vez
    de colgarse: con el enfoque anterior (randint en bucle hasta juntar
    `cantidad` posiciones distintas) esa situacion nunca converge.
    """
    return set(random.sample(range(1, HUECOS + 1), cantidad))


def elegir_posicion() -> int:
    """Pide al jugador una posicion valida del tambor."""
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
        return posicion


def escena(ronda: int, balas: int) -> None:
    """Limpia la pantalla y dibuja la cabecera y el tambor de la ronda."""
    limpiar()
    cabecera(ronda, balas)
    print()
    print(_c("   La bala descansa en un hueco. Tu huella deja marcas.", GRIS))
    dibujar_tambor()
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


def jugar_partida() -> bool:
    """Juega una partida completa, ronda a ronda, hasta que el jugador
    muere o sobrevive las RONDAS. Devuelve True si sobrevive (victoria),
    False si muere en el camino (derrota) -- no decide que hacer con ese
    resultado (pantalla de victoria, preguntar si se quiere repetir...),
    de eso se encarga jugar().
    """
    for ronda in range(1, RONDAS + 1):
        balas = ronda
        posiciones_bala = colocar_balas(balas)

        escena(ronda, balas)
        elegida = elegir_posicion()

        if elegida in posiciones_bala:
            fracaso(ronda)
            input(_c("   Pulsa Enter para volver a empezar...", NEGRITA))
            return False

        if ronda < RONDAS:
            print(
                _c(
                    f"   Click. Cartucho vacio. Avanzas a la ronda {ronda + 1}.",
                    VERDE,
                )
            )
            time.sleep(1.5)

    return True


def jugar() -> None:
    """Ejecuta el bucle principal del juego hasta que el jugador se retira."""
    while True:
        gano = jugar_partida()

        if gano:
            victoria()
            otra = input(_c("   Volver a jugar? (s/n): ", NEGRITA)).strip().lower()
            if otra not in ("s", "si", "y", "yes"):
                print(_c("   Hasta la proxima. El tambor siempre espera.", AMARILLO))
                break


def main() -> None:
    """Punto de entrada real del juego (usado por `run.sh`/`run.bat` via
    `__main__` y por el comando `ruleta` instalable via pyproject.toml):
    envuelve jugar() para que Ctrl+C siempre salga con el mensaje de
    despedida en vez de un traceback, sin importar por cual de las dos
    vias se haya lanzado.
    """
    try:
        jugar()
    except KeyboardInterrupt:
        print()
        print(_c("   Hasta la proxima. El tambor siempre espera.", AMARILLO))


if __name__ == "__main__":
    main()
