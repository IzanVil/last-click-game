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


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def dibujar_tambor(marcadas):
    marco = "┌" + "─┬" * (HUECOS - 1) + "─┐"
    celdas = []
    etiquetas = []
    for i in range(1, HUECOS + 1):
        if i in marcadas:
            celdas.append(GRIS + "·" + RESET)
        else:
            celdas.append(CELESTE + "0" + RESET)
        etiquetas.append(str(i))
    print("   " + NEGRITA + marco + RESET)
    print("   " + "   ".join(celdas))
    print("   " + NEGRITA + "└" + "─┴" * (HUECOS - 1) + "─┘" + RESET)
    print("   " + "  ".join(etiquetas))


def cabecera(ronda, balas):
    print(NEGRITA + CELESTE + "╔" + "═" * 44 + "╗" + RESET)
    print(NEGRITA + CELESTE + "║" + RESET + "            RULETA RUSA              " + NEGRITA + CELESTE + "║" + RESET)
    print(NEGRITA + CELESTE + "║" + RESET + "   Ronda " + AMARILLO + f"{ronda:^2}" + RESET + "/" + str(RONDAS) + "  ·  Balas " + ROJO + f"{balas:^2}" + RESET + "  ·  Vacios " + VERDE + f"{HUECOS - balas:^2}" + RESET + "  " + NEGRITA + CELESTE + "║" + RESET)
    print(NEGRITA + CELESTE + "╚" + "═" * 44 + "╝" + RESET)


def colocar_balas(cantidad):
    posiciones = set()
    while len(posiciones) < cantidad:
        posiciones.add(random.randint(1, HUECOS))
    return posiciones


def elegir_posicion(marcadas):
    while True:
        entrada = input(NEGRITA + "   Elige una posicion (1-" + str(HUECOS) + "): " + RESET).strip()
        try:
            posicion = int(entrada)
        except ValueError:
            print(ROJO + "   Eso no parece un numero." + RESET)
            continue
        if posicion < 1 or posicion > HUECOS:
            print(ROJO + "   Ese numero no esta en el tambor." + RESET)
            continue
        if posicion in marcadas:
            print(AMARILLO + "   Ya has probado esa posicion." + RESET)
            continue
        return posicion


def escena(ronda, balas, marcadas):
    limpiar()
    cabecera(ronda, balas)
    print()
    print(GRIS + "   La bala descansa en un hueco. Tu huella deja marcas." + RESET)
    dibujar_tambor(marcadas)
    print()


def fracaso(ronda):
    limpiar()
    print(NEGRITA + ROJO + "\n      ▓▓▓   B O O M   ▓▓▓\n" + RESET)
    print(ROJO + "   La bala ha encontrado tu numero.")
    print(AMARILLO + "   Caiste en la ronda " + str(ronda) + " de " + str(RONDAS) + ".\n")
    time.sleep(2)


def victoria():
    limpiar()
    print(NEGRITA + VERDE + "\n    ✦  HAS SOBREVIVIDO  ✦\n" + RESET)
    print(CELESTE + "   Superaste las " + str(RONDAS) + " rondas del tambor.")
    print(VERDE + "   No eres de este mundo. Eres una leyenda.\n")
    time.sleep(2)


def jugar():
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
                input(NEGRITA + "   Pulsa Enter para volver a empezar..." + RESET)
                break

            print(VERDE + "   Click. Cartucho vacio. Avanzas a la ronda " + str(ronda + 1) + "." + RESET)
            time.sleep(1.5)
            ronda += 1

        if ronda > RONDAS:
            victoria()
            otra = input(NEGRITA + "   Volver a jugar? (s/n): " + RESET).strip().lower()
            if otra not in ("s", "si", "y", "yes"):
                print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)
                break


if __name__ == "__main__":
    try:
        jugar()
    except KeyboardInterrupt:
        print()
        print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)
