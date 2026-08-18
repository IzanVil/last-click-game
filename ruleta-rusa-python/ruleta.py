import random


def jugar():
    posicion_bala = random.randint(1, 6)

    print("=== RULETA RUSA ===")
    print("La bala esta en una posicion del 1 al 6.")
    print("Elige un numero y cruza los dedos.\n")

    while True:
        try:
            eleccion = int(input("Numero del 1 al 6: "))
            if not 1 <= eleccion <= 6:
                print("Ese numero no esta en el tambor. Intenta otra vez.\n")
                continue
            break
        except ValueError:
            print("Eso no parece un numero. Intenta otra vez.\n")

    if eleccion == posicion_bala:
        print("\nBOOM. La bala estaba en", posicion_bala, ". Esta vez no hubo suerte.\n")
    else:
        print("\nClick. Solo fue un cartucho vacio. Sobreviviste a la posicion", eleccion, ".\n")

    otra = input("Volver a jugar? (s/n): ").strip().lower()
    print()
    if otra in ("s", "si", "y", "yes"):
        jugar()


if __name__ == "__main__":
    jugar()
