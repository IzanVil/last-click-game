"""Interfaz de terminal de "El Tambor del Juicio".

Este archivo solo se ocupa de entrada/salida (pantalla, teclado, colores y
pausas); la logica del juego vive en estado.py, pistas.py, apuestas.py,
farol.py, eventos.py, historial.py y records.py.

El try/except de abajo permite que el modulo funcione tanto instalado como
paquete (`terminal.ruleta`, con imports relativos) como ejecutado suelto
(`python3 ruleta.py` desde dentro de `terminal/`, sin paquete que valga).
"""

import argparse
import os
import time
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version

try:
    from . import apuestas, estado, eventos, farol, historial, pistas, records
except ImportError:  # pragma: no cover - ejecucion como script suelto
    # mypy resuelve el paquete via el `from .` de arriba y no encuentra
    # estos como modulos sueltos de nivel superior (solo existen asi en
    # tiempo de ejecucion, cuando este archivo corre como script suelto
    # con `terminal/` en sys.path): son el mismo modulo por las dos vias,
    # asi que ignorarlo aqui es correcto y no un error real.
    import apuestas  # type: ignore[no-redef,import-not-found]
    import estado  # type: ignore[no-redef,import-not-found]
    import eventos  # type: ignore[no-redef,import-not-found]
    import farol  # type: ignore[no-redef,import-not-found]
    import historial  # type: ignore[no-redef,import-not-found]
    import pistas  # type: ignore[no-redef,import-not-found]
    import records  # type: ignore[no-redef,import-not-found]

APUESTA_BASE = 100
BONO_MARCA_ACERTADA = 50

# Presets de dificultad: huecos del tambor y marcas de farol por partida.
# --huecos/--marcas explicitos en la CLI pisan el valor del preset (ver
# _parsear_args).
DIFICULTADES = {
    "facil": {"huecos": 10, "marcas": 4},
    "normal": {"huecos": estado.HUECOS, "marcas": farol.MARCAS_INICIALES},
    "dificil": {"huecos": 6, "marcas": 2},
}

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


if os.name == "nt":
    # Habilita el procesamiento VT100 (codigos ANSI) en cmd.exe moderno:
    # es un efecto secundario documentado de esta llamada "vacia", sin
    # necesitar ninguna dependencia extra (colorama, etc.). Sin esto, en
    # un cmd.exe "clasico" los codigos de color de abajo se verian
    # literales en pantalla en vez de colorear.
    os.system("")


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
        estado_hueco = estados.get(i, "")
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
    _imprimir_pistas(pistas_reveladas)
    print()
    dibujar_tambor(estados, huecos)
    print()


def _imprimir_pistas(pistas_reveladas: list["pistas.Pista"]) -> None:
    """Imprime la lista de pistas acumuladas, o el aviso de que aun no
    hay ninguna. Comun a la partida en solitario y al modo duelo."""
    if pistas_reveladas:
        print(NEGRITA + "   Pistas del tambor:" + RESET)
        for indice, pista in enumerate(pistas_reveladas, start=1):
            print(f"   {AMARILLO}#{indice}{RESET} {pista.texto}")
    else:
        print(GRIS + "   La bala descansa en algun hueco. Aun no hay pistas." + RESET)


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


def impacto(
    disparos: int,
    perdidos: int,
    dias: int,
    resumen_texto: str,
    nuevo_record: bool = False,
) -> None:
    """Muestra la pantalla de derrota (BOOM), lo perdido y el resumen final."""
    limpiar()
    print(NEGRITA + ROJO + "\n      ▓▓▓   B O O M   ▓▓▓\n" + RESET)
    print(ROJO + "   La bala ha encontrado tu numero." + RESET)
    print(
        f"{AMARILLO}   Caiste tras {disparos} disparo(s) ({dias} dia(s) "
        f"sobrevivido(s)), perdiendo {perdidos} puntos.{RESET}"
    )
    if nuevo_record:
        print(NEGRITA + AMARILLO + "   ¡Nuevo record de dias sobrevividos!" + RESET)
    print(f"{CELESTE}   {resumen_texto}\n{RESET}")
    time.sleep(2)


def retirada(
    disparos: int,
    ganados: int,
    dias: int,
    resumen_texto: str,
    nuevo_record: bool = False,
) -> None:
    """Muestra la pantalla de retirada, lo cobrado y el resumen final."""
    limpiar()
    print(NEGRITA + VERDE + "\n    ✦  TE RETIRAS A TIEMPO  ✦\n" + RESET)
    print(
        f"{CELESTE}   Cobras {ganados} puntos tras {disparos} disparo(s) "
        f"({dias} dia(s) sobrevivido(s)).{RESET}"
    )
    if nuevo_record:
        print(NEGRITA + AMARILLO + "   ¡Nuevo record de dias sobrevividos!" + RESET)
    print(f"{VERDE}   {resumen_texto}\n{RESET}")
    time.sleep(2)


def jugar(huecos: int = estado.HUECOS, marcas: int = farol.MARCAS_INICIALES) -> None:
    """Ejecuta el bucle principal: disparar, marcar o retirarse."""
    misrecords = records.cargar()

    while True:
        tambor = estado.TamborJuicio(huecos=huecos)
        apuesta = apuestas.Apuesta(APUESTA_BASE)
        marca = farol.Farol(marcas)
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
                nuevo_record = dias > misrecords.dias_maximos
                misrecords.registrar_partida(
                    dias, ganados, bitacora.faroles_usados, bitacora.faroles_acertados
                )
                records.guardar(misrecords)
                retirada(
                    disparos,
                    ganados,
                    dias,
                    historial.resumen(bitacora, dias),
                    nuevo_record,
                )
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
                nuevo_record = dias > misrecords.dias_maximos
                misrecords.registrar_partida(
                    dias, perdidos, bitacora.faroles_usados, bitacora.faroles_acertados
                )
                records.guardar(misrecords)
                impacto(
                    disparos,
                    perdidos,
                    dias,
                    historial.resumen(bitacora, dias),
                    nuevo_record,
                )
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


@dataclass
class JugadorDuelo:
    """Estado de un jugador dentro de una partida de modo duelo.

    Cada jugador lleva su propia apuesta, sus propias marcas de farol y
    su propio contador de disparos (sus "dias de vida" son solo los
    disparos que ha sobrevivido el mismo); el tambor, sus pistas y los
    huecos ya marcados o disparados son compartidos entre los dos (ver
    jugar_duelo).
    """

    nombre: str
    apuesta: "apuestas.Apuesta"
    marca: "farol.Farol"
    bitacora: "historial.Historial" = field(default_factory=historial.Historial)
    disparos: int = 0
    puntos_finales: int = 0

    @property
    def dias(self) -> int:
        return estado.dias_sobrevividos(self.disparos)


def _pedir_nombre(numero: int) -> str:
    """Pide el nombre de un jugador; en blanco usa 'Jugador N'."""
    prefijo = f"Nombre del jugador {numero} (Enter para 'Jugador {numero}'): "
    entrada = input(f"{NEGRITA}   {prefijo}{RESET}").strip()
    return entrada or f"Jugador {numero}"


def escena_duelo(
    activo: JugadorDuelo,
    rival: JugadorDuelo,
    estados: dict[int, str],
    pistas_reveladas: list["pistas.Pista"],
    huecos: int,
) -> None:
    """Como escena(), pero para el modo duelo: añade de quien es el turno
    y el estado del rival por encima del tablero, que es compartido."""
    limpiar()
    print(NEGRITA + CELESTE + "   === EL TAMBOR DEL JUICIO: DUELO ===" + RESET)
    print(
        f"{AMARILLO}   Turno de {activo.nombre}{RESET}   ·   "
        f"{rival.nombre}: {rival.dias} dia(s) sobrevividos"
    )
    print()
    cabecera(activo.disparos, activo.apuesta, activo.marca)
    print()
    _imprimir_pistas(pistas_reveladas)
    print()
    dibujar_tambor(estados, huecos)
    print()


def resultado_duelo(jugadores: list[JugadorDuelo]) -> None:
    """Compara a los jugadores (dias sobrevividos y, en caso de empate,
    puntos alcanzados) y muestra quien gana el duelo."""
    limpiar()
    print(NEGRITA + AMARILLO + "\n   === RESULTADO DEL DUELO ===\n" + RESET)
    for jugador in jugadores:
        print(
            f"   {jugador.nombre}: {jugador.dias} dia(s) sobrevividos, "
            f"{jugador.puntos_finales} puntos."
        )
    print()

    mejor_dias = max(j.dias for j in jugadores)
    finalistas = [j for j in jugadores if j.dias == mejor_dias]
    if len(finalistas) > 1:
        mejores_puntos = max(j.puntos_finales for j in finalistas)
        finalistas = [j for j in finalistas if j.puntos_finales == mejores_puntos]

    if len(finalistas) > 1:
        print(NEGRITA + CELESTE + "   Empate. El tambor no se decide." + RESET)
    else:
        print(NEGRITA + VERDE + f"   ¡Gana {finalistas[0].nombre}!" + RESET)
    print()
    time.sleep(1)
    input(NEGRITA + "   Pulsa Enter para continuar..." + RESET)


def jugar_duelo(
    huecos: int = estado.HUECOS, marcas: int = farol.MARCAS_INICIALES
) -> None:
    """Modo duelo: dos jugadores turnandose en el mismo tambor.

    El tambor, sus pistas y los huecos ya marcados o disparados son
    compartidos (es literalmente el mismo revolver); cada jugador tiene
    su propia apuesta, marcas y contador de disparos. La partida termina
    en cuanto el turno de uno de los dos acaba en impacto o retirada: no
    sigue jugando el otro en solitario despues. Se compara quien
    sobrevivio mas dias (y, en caso de empate, quien llego con mas
    puntos) para decidir quien gana.
    """
    misrecords = records.cargar()

    limpiar()
    print(NEGRITA + CELESTE + "\n   === EL TAMBOR DEL JUICIO: DUELO ===\n" + RESET)
    nombres = [_pedir_nombre(1), _pedir_nombre(2)]

    while True:
        tambor = estado.TamborJuicio(huecos=huecos)
        pistas_reveladas: list[pistas.Pista] = []
        marcadas: set[int] = set()
        resultados_farol: dict[int, str] = {}
        jugadores = [
            JugadorDuelo(
                nombres[0], apuestas.Apuesta(APUESTA_BASE), farol.Farol(marcas)
            ),
            JugadorDuelo(
                nombres[1], apuestas.Apuesta(APUESTA_BASE), farol.Farol(marcas)
            ),
        ]

        turno = 0
        while True:
            activo = jugadores[turno % 2]
            rival = jugadores[(turno + 1) % 2]

            candidatos = pistas.interseccion(pistas_reveladas)
            estados = calcular_estados(marcadas, resultados_farol, candidatos)
            escena_duelo(activo, rival, estados, pistas_reveladas, tambor.huecos)
            accion = elegir_accion(activo.marca.marcas_restantes)

            if accion == "retirarse":
                activo.puntos_finales = activo.apuesta.retirarse()
                nuevo_record = activo.dias > misrecords.dias_maximos
                misrecords.registrar_partida(
                    activo.dias,
                    activo.puntos_finales,
                    activo.bitacora.faroles_usados,
                    activo.bitacora.faroles_acertados,
                )
                records.guardar(misrecords)
                retirada(
                    activo.disparos,
                    activo.puntos_finales,
                    activo.dias,
                    historial.resumen(activo.bitacora, activo.dias),
                    nuevo_record,
                )
                break

            if accion == "marcar":
                posicion = elegir_posicion(tambor.huecos)
                acierto = activo.marca.marcar(posicion, tambor.posicion_bala)
                activo.bitacora.registrar_farol(acierto)
                resultados_farol[posicion] = "seguro" if acierto else "peligro"
                if acierto:
                    activo.apuesta.sumar_bono(BONO_MARCA_ACERTADA)
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
                turno += 1
                continue

            posicion = elegir_posicion(tambor.huecos)
            marcadas.add(posicion)
            activo.disparos += 1

            if tambor.disparar(posicion):
                activo.puntos_finales = activo.apuesta.perder()
                nuevo_record = activo.dias > misrecords.dias_maximos
                misrecords.registrar_partida(
                    activo.dias,
                    activo.puntos_finales,
                    activo.bitacora.faroles_usados,
                    activo.bitacora.faroles_acertados,
                )
                records.guardar(misrecords)
                impacto(
                    activo.disparos,
                    activo.puntos_finales,
                    activo.dias,
                    historial.resumen(activo.bitacora, activo.dias),
                    nuevo_record,
                )
                break

            activo.apuesta.doblar()

            evento = eventos.tirar_evento()
            if evento == "clic_metalico":
                tambor.mover_extra()
            if evento is not None:
                activo.bitacora.registrar_evento(evento)
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
                f"a {activo.apuesta.en_juego} puntos.{RESET}"
            )
            time.sleep(1.5)
            turno += 1

        # El rival no jugo su ultimo turno con los mismos puntos "en
        # juego" que ya se le hubiesen esfumado o cobrado: para el, sus
        # puntos finales son los que llevaba en juego cuando el duelo
        # termino (no jugo ni impacto ni retirada, sigue "vivo" a medias).
        rival.puntos_finales = rival.apuesta.en_juego
        resultado_duelo(jugadores)

        otra = input(NEGRITA + "   Jugar otro duelo? (s/n): " + RESET).strip().lower()
        if otra not in ("s", "si", "y", "yes"):
            print(f"{AMARILLO}   Hasta la proxima. El tambor siempre espera.{RESET}")
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
    """Define y valida las opciones de la CLI.

    Separado de main() para poder testearlo pasandole `argv` a mano, sin
    tocar el sys.argv real del proceso.
    """
    parser = argparse.ArgumentParser(
        prog="ruleta",
        description=(
            "El Tambor del Juicio: dispara, marca faroles o retirate, "
            "deduce el patron de la bala y sobrevive tantos dias como "
            "te atrevas."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_texto()}",
    )
    parser.add_argument(
        "--dificultad",
        choices=sorted(DIFICULTADES),
        default="normal",
        help="Preset de huecos y marcas (por defecto: normal). Ver --huecos/--marcas.",
    )
    parser.add_argument(
        "--huecos",
        type=int,
        default=None,
        help="Huecos del tambor (por defecto, segun --dificultad).",
    )
    parser.add_argument(
        "--marcas",
        type=int,
        default=None,
        help="Marcas de farol por partida (por defecto, segun --dificultad).",
    )
    parser.add_argument(
        "--duelo",
        action="store_true",
        help="Modo duelo: dos jugadores turnandose en el mismo tambor.",
    )
    parser.add_argument(
        "--records",
        action="store_true",
        help="Muestra los records guardados y termina, sin jugar.",
    )
    args = parser.parse_args(argv)

    preset = DIFICULTADES[args.dificultad]
    if args.huecos is None:
        args.huecos = preset["huecos"]
    if args.marcas is None:
        args.marcas = preset["marcas"]

    if args.huecos < 2:
        # Mismo mensaje que TamborJuicio.__init__, pero convertido al
        # idioma de error de argparse (exit code 2) en vez de dejar que
        # un ValueError suelto reviente a mitad de partida.
        parser.error(f"huecos debe ser al menos 2 (recibido: {args.huecos}).")
    if args.marcas < 0:
        parser.error(f"marcas no puede ser negativo (recibido: {args.marcas}).")

    return args


def main(argv: list[str] | None = None) -> None:
    """Punto de entrada real del juego (usado por `run.sh`/`run.bat` via
    `__main__` y por el comando `ruleta` instalable via pyproject.toml):
    envuelve jugar()/jugar_duelo() para que Ctrl+C siempre salga con el
    mensaje de despedida en vez de un traceback, sin importar por cual
    de las dos vias se haya lanzado. `argv=None` hace que argparse lea
    sys.argv real (comportamiento normal); se le puede pasar una lista
    para lanzar el juego con otros parametros sin pasar por la terminal.
    """
    args = _parsear_args(argv)

    if args.records:
        print(records.resumen(records.cargar()))
        return

    try:
        if args.duelo:
            jugar_duelo(huecos=args.huecos, marcas=args.marcas)
        else:
            jugar(huecos=args.huecos, marcas=args.marcas)
    except KeyboardInterrupt:
        print()
        print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)


if __name__ == "__main__":
    main()
