"""Interfaz de terminal de "El Tambor del Juicio".

Este archivo solo se ocupa de entrada/salida (pantalla, teclado, colores y
pausas); la logica del juego vive en estado.py, pistas.py, apuestas.py,
farol.py, eventos.py e historial.py.

El try/except de abajo permite que el modulo funcione tanto instalado como
paquete (`terminal.ruleta`, con imports relativos) como ejecutado suelto
(`python3 ruleta.py` desde dentro de `terminal/`, sin paquete que valga).
"""

import os
import time

try:
    from . import apuestas, estado, eventos, farol, historial, pistas
except ImportError:  # pragma: no cover - ejecucion como script suelto
    import apuestas
    import estado
    import eventos
    import farol
    import historial
    import pistas

APUESTA_BASE = 100
BONO_MARCA_ACERTADA = 50

ROJO = "\033[91m"
VERDE = "\033[92m"
AMARILLO = "\033[93m"
CELESTE = "\033[96m"
GRIS = "\033[90m"
NEGRITA = "\033[1m"
RESET = "\033[0m"

# Como se ve cada hueco segun lo que se sabe de el (ver calcular_estados).
GLIFOS_ESTADO = {"seguro": "✓", "peligro": "✗", "candidato": "?", "probado": "·"}
COLORES_ESTADO = {
    "seguro": VERDE,
    "peligro": ROJO,
    "candidato": AMARILLO,
    "probado": GRIS,
}


def limpiar() -> None:
    """Limpia la pantalla de la terminal segun el sistema operativo."""
    os.system("cls" if os.name == "nt" else "clear")


def calcular_estados(
    marcadas: set[int], resultados_farol: dict[int, str], candidatos: frozenset[int]
) -> dict[int, str]:
    """Combina lo que se sabe de cada hueco en un unico estado para pintarlo.

    Prioridad, de menos a mas fiable: ser candidato segun las pistas
    actuales, haber sido ya disparado, y por encima de todo un resultado
    de farol (seguro/peligro), que es la unica confirmacion directa.
    """
    estados: dict[int, str] = {hueco: "candidato" for hueco in candidatos}
    for hueco in marcadas:
        estados[hueco] = "probado"
    estados.update(resultados_farol)
    return estados


def dibujar_tambor(estados: dict[int, str], huecos: int) -> None:
    """Imprime el tambor ASCII coloreando cada hueco segun `estados`.

    Verde = farol acertado ahi, rojo = farol fallido ahi (la bala estuvo
    en ese momento), amarillo = candidato segun las pistas actuales, gris
    = ya disparado. Sin ninguna marca, se muestra sin colorear.
    """
    marco = "┌" + "─┬" * (huecos - 1) + "─┐"
    celdas = []
    etiquetas = []
    for i in range(1, huecos + 1):
        estado_hueco = estados.get(i)
        color = COLORES_ESTADO.get(estado_hueco, CELESTE)
        glifo = GLIFOS_ESTADO.get(estado_hueco, "0")
        celdas.append(color + glifo + RESET)
        etiquetas.append(str(i))
    print("   " + NEGRITA + marco + RESET)
    print("   " + "   ".join(celdas))
    print("   " + NEGRITA + "└" + "─┴" * (huecos - 1) + "─┘" + RESET)
    print("   " + "  ".join(etiquetas))


def cabecera(disparos: int, apuesta: "apuestas.Apuesta", marca: "farol.Farol") -> None:
    """Imprime el marco superior con el dia actual, marcas y lo apostado."""
    dia = estado.dias_sobrevividos(disparos) + 1
    disparo_del_dia = disparos % estado.DISPAROS_POR_DIA + 1
    print(f"{NEGRITA}{CELESTE}╔{'═' * 44}╗{RESET}")
    print(
        f"{NEGRITA}{CELESTE}║{RESET}"
        "        EL TAMBOR DEL JUICIO         "
        f"{NEGRITA}{CELESTE}║{RESET}"
    )
    print(
        f"{NEGRITA}{CELESTE}║{RESET}   Dia {AMARILLO}{dia:^2}{RESET}"
        f" (disparo {disparo_del_dia}/{estado.DISPAROS_POR_DIA})"
        f"  ·  Marcas {CELESTE}{marca.marcas_restantes}{RESET}  "
        f"{NEGRITA}{CELESTE}║{RESET}"
    )
    print(
        f"{NEGRITA}{CELESTE}║{RESET}   En juego "
        f"{VERDE}{apuesta.en_juego:>5}{RESET} pts"
        f"{' ' * 20}{NEGRITA}{CELESTE}║{RESET}"
    )
    print(f"{NEGRITA}{CELESTE}╚{'═' * 44}╝{RESET}")


def escena(
    disparos: int,
    apuesta: "apuestas.Apuesta",
    marca: "farol.Farol",
    estados: dict[int, str],
    pistas_reveladas: list["pistas.Pista"],
    huecos: int,
) -> None:
    """Limpia la pantalla y dibuja la cabecera, las pistas y el tambor."""
    limpiar()
    cabecera(disparos, apuesta, marca)
    print()
    if pistas_reveladas:
        print(NEGRITA + "   Pistas del tambor:" + RESET)
        for indice, pista in enumerate(pistas_reveladas, start=1):
            print(f"   {AMARILLO}#{indice}{RESET} {pista.texto}")
    else:
        print(GRIS + "   La bala descansa en algun hueco. Aun no hay pistas." + RESET)
    print()
    dibujar_tambor(estados, huecos)
    print()


def elegir_accion(marcas_restantes: int) -> str:
    """Pide al jugador si dispara, se retira o (si le quedan) marca."""
    if marcas_restantes > 0:
        opciones = f"(D)isparar, (R)etirarse o (M)arcar [{marcas_restantes}]"
    else:
        opciones = "(D)isparar o (R)etirarse"
    while True:
        entrada = input(f"{NEGRITA}   {opciones}: {RESET}").strip().lower()
        if entrada in ("d", "disparar"):
            return "disparar"
        if entrada in ("r", "retirarse"):
            return "retirarse"
        if marcas_restantes > 0 and entrada in ("m", "marcar"):
            return "marcar"
        print(ROJO + "   Esa respuesta no esta entre las opciones." + RESET)


def elegir_posicion(huecos: int) -> int:
    """Pide al jugador una posicion valida del tambor."""
    while True:
        entrada = input(f"{NEGRITA}   Elige una posicion (1-{huecos}): {RESET}").strip()
        try:
            posicion = int(entrada)
        except ValueError:
            print(ROJO + "   Eso no parece un numero." + RESET)
            continue
        if posicion < 1 or posicion > huecos:
            print(ROJO + "   Ese numero no esta en el tambor." + RESET)
            continue
        return posicion


def impacto(disparos: int, perdidos: int, dias: int, resumen_texto: str) -> None:
    """Muestra la pantalla de derrota (BOOM), lo perdido y el resumen final."""
    limpiar()
    print(NEGRITA + ROJO + "\n      ▓▓▓   B O O M   ▓▓▓\n" + RESET)
    print(ROJO + "   La bala ha encontrado tu numero." + RESET)
    print(
        f"{AMARILLO}   Caiste tras {disparos} disparo(s) ({dias} dia(s) "
        f"sobrevivido(s)), perdiendo {perdidos} puntos.{RESET}"
    )
    print(f"{CELESTE}   {resumen_texto}\n{RESET}")
    time.sleep(2)


def retirada(disparos: int, ganados: int, dias: int, resumen_texto: str) -> None:
    """Muestra la pantalla de retirada, lo cobrado y el resumen final."""
    limpiar()
    print(NEGRITA + VERDE + "\n    ✦  TE RETIRAS A TIEMPO  ✦\n" + RESET)
    print(
        f"{CELESTE}   Cobras {ganados} puntos tras {disparos} disparo(s) "
        f"({dias} dia(s) sobrevivido(s)).{RESET}"
    )
    print(f"{VERDE}   {resumen_texto}\n{RESET}")
    time.sleep(2)


def jugar() -> None:
    """Ejecuta el bucle principal: disparar, marcar o retirarse."""
    while True:
        tambor = estado.TamborJuicio()
        apuesta = apuestas.Apuesta(APUESTA_BASE)
        marca = farol.Farol()
        bitacora = historial.Historial()
        disparos = 0
        marcadas: set[int] = set()
        resultados_farol: dict[int, str] = {}
        pistas_reveladas: list[pistas.Pista] = []

        while True:
            candidatos = pistas.interseccion(pistas_reveladas)
            estados = calcular_estados(marcadas, resultados_farol, candidatos)
            escena(disparos, apuesta, marca, estados, pistas_reveladas, tambor.huecos)
            accion = elegir_accion(marca.marcas_restantes)

            if accion == "retirarse":
                ganados = apuesta.retirarse()
                dias = estado.dias_sobrevividos(disparos)
                retirada(disparos, ganados, dias, historial.resumen(bitacora, dias))
                break

            if accion == "marcar":
                posicion = elegir_posicion(tambor.huecos)
                acierto = marca.marcar(posicion, tambor.posicion_bala)
                bitacora.registrar_farol(acierto)
                resultados_farol[posicion] = "seguro" if acierto else "peligro"
                if acierto:
                    apuesta.sumar_bono(BONO_MARCA_ACERTADA)
                    print(
                        f"{VERDE}   Farol acertado: el hueco {posicion} estaba "
                        f"vacio. +{BONO_MARCA_ACERTADA} puntos.{RESET}"
                    )
                else:
                    print(
                        f"{ROJO}   Farol fallido: ahi estaba la bala. "
                        f"Pierdes la marca.{RESET}"
                    )
                time.sleep(1.5)
                continue

            posicion = elegir_posicion(tambor.huecos)
            marcadas.add(posicion)
            disparos += 1

            if tambor.disparar(posicion):
                perdidos = apuesta.perder()
                dias = estado.dias_sobrevividos(disparos)
                impacto(disparos, perdidos, dias, historial.resumen(bitacora, dias))
                break

            apuesta.doblar()

            evento = eventos.tirar_evento()
            if evento == "clic_metalico":
                tambor.mover_extra()
            if evento is not None:
                bitacora.registrar_evento(evento)
                print(f"{GRIS}   {eventos.texto_de(evento)}{RESET}")

            pistas_reveladas.append(
                pistas.generar_pista(
                    tambor.posicion_bala,
                    tambor.huecos,
                    tambor.ultimo_disparo,
                    mentir=(evento == "tambor_caliente"),
                )
            )
            print(
                f"{VERDE}   Click. Cartucho vacio. Lo apostado se dobla "
                f"a {apuesta.en_juego} puntos.{RESET}"
            )
            if disparos % estado.DISPAROS_POR_DIA == 0:
                print(
                    f"{AMARILLO}   Sobrevives al dia "
                    f"{estado.dias_sobrevividos(disparos)}.{RESET}"
                )
            time.sleep(1.5)

        otra = input(NEGRITA + "   Jugar otra partida? (s/n): " + RESET).strip().lower()
        if otra not in ("s", "si", "y", "yes"):
            print(f"{AMARILLO}   Hasta la proxima. El tambor siempre espera.{RESET}")
            break


if __name__ == "__main__":
    try:
        jugar()
    except KeyboardInterrupt:
        print()
        print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)
