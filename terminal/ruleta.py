import os
import random
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


def limpiar() -> None:
    """Limpia la pantalla de la terminal segun el sistema operativo."""
    os.system("cls" if os.name == "nt" else "clear")


def dibujar_tambor() -> None:
    """Imprime el tambor ASCII con sus huecos numerados."""
    marco = "┌" + "─┬" * (HUECOS - 1) + "─┐"
    celdas = []
    etiquetas = []
    for i in range(1, HUECOS + 1):
        celdas.append(CELESTE + "0" + RESET)
        etiquetas.append(str(i))
    print("   " + NEGRITA + marco + RESET)
    print("   " + "   ".join(celdas))
    print("   " + NEGRITA + "└" + "─┴" * (HUECOS - 1) + "─┘" + RESET)
    print("   " + "  ".join(etiquetas))


def cabecera(ronda: int, balas: int) -> None:
    """Imprime el marco superior con la ronda actual, balas y huecos vacios."""
    vacios = HUECOS - balas
    print(f"{NEGRITA}{CELESTE}╔{'═' * 44}╗{RESET}")
    print(
        f"{NEGRITA}{CELESTE}║{RESET}"
        "            RULETA RUSA              "
        f"{NEGRITA}{CELESTE}║{RESET}"
    )
    print(
        f"{NEGRITA}{CELESTE}║{RESET}   Ronda {AMARILLO}{ronda:^2}{RESET}/{RONDAS}"
        f"  ·  Balas {ROJO}{balas:^2}{RESET}  ·  Vacios {VERDE}{vacios:^2}{RESET}  "
        f"{NEGRITA}{CELESTE}║{RESET}"
    )
    print(f"{NEGRITA}{CELESTE}╚{'═' * 44}╝{RESET}")


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
        entrada = input(f"{NEGRITA}   Elige una posicion (1-{HUECOS}): {RESET}").strip()
        try:
            posicion = int(entrada)
        except ValueError:
            print(ROJO + "   Eso no parece un numero." + RESET)
            continue
        if posicion < 1 or posicion > HUECOS:
            print(ROJO + "   Ese numero no esta en el tambor." + RESET)
            continue
        return posicion


def escena(ronda: int, balas: int) -> None:
    """Limpia la pantalla y dibuja la cabecera y el tambor de la ronda."""
    limpiar()
    cabecera(ronda, balas)
    print()
    print(GRIS + "   La bala descansa en un hueco. Tu huella deja marcas." + RESET)
    dibujar_tambor()
    print()


def fracaso(ronda: int) -> None:
    """Muestra la pantalla de derrota (BOOM) para la ronda indicada."""
    limpiar()
    print(NEGRITA + ROJO + "\n      ▓▓▓   B O O M   ▓▓▓\n" + RESET)
    print(ROJO + "   La bala ha encontrado tu numero.")
    print(f"{AMARILLO}   Caiste en la ronda {ronda} de {RONDAS}.\n")
    time.sleep(2)


def victoria() -> None:
    """Muestra la pantalla de victoria tras superar todas las rondas."""
    limpiar()
    print(NEGRITA + VERDE + "\n    ✦  HAS SOBREVIVIDO  ✦\n" + RESET)
    print(CELESTE + "   Superaste las " + str(RONDAS) + " rondas del tambor.")
    print(VERDE + "   No eres de este mundo. Eres una leyenda.\n")
    time.sleep(2)


def jugar() -> None:
    """Ejecuta el bucle principal del juego hasta que el jugador se retira."""
    while True:
        ronda = 1

        while ronda <= RONDAS:
            balas = ronda
            posiciones_bala = colocar_balas(balas)

            escena(ronda, balas)
            elegida = elegir_posicion()

            if elegida in posiciones_bala:
                fracaso(ronda)
                input(NEGRITA + "   Pulsa Enter para volver a empezar..." + RESET)
                break

            print(
                f"{VERDE}   Click. Cartucho vacio. Avanzas a la ronda "
                f"{ronda + 1}.{RESET}"
            )
            time.sleep(1.5)
            ronda += 1

        if ronda > RONDAS:
            victoria()
            otra = input(NEGRITA + "   Volver a jugar? (s/n): " + RESET).strip().lower()
            if otra not in ("s", "si", "y", "yes"):
                print(
                    f"{AMARILLO}   Hasta la proxima. El tambor siempre espera.{RESET}"
                )
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
        print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)


if __name__ == "__main__":
    main()
