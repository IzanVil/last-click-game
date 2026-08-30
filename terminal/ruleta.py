"""Interfaz de terminal de "El Tambor del Juicio".

Este archivo solo se ocupa de entrada/salida (pantalla, teclado, colores,
animaciones y pausas); la logica del juego vive en estado.py, pistas.py,
apuestas.py, farol.py, eventos.py, historial.py y records.py, y las
primitivas de terminal (limpiar, teclear letra a letra, pitar, repintar
un bloque) en efectos.py, entrada.py y ambiente.py.

El try/except de abajo permite que el modulo funcione tanto instalado como
paquete (`terminal.ruleta`, con imports relativos) como ejecutado suelto
(`python3 ruleta.py` desde dentro de `terminal/`, sin paquete que valga).
"""

import argparse
import os
import textwrap
from dataclasses import dataclass, field
from functools import partial
from importlib.metadata import PackageNotFoundError, version

try:
    from . import (
        ambiente,
        apuestas,
        efectos,
        entrada,
        estado,
        eventos,
        farol,
        historial,
        pistas,
        records,
    )
except ImportError:  # pragma: no cover - ejecucion como script suelto
    # mypy resuelve el paquete via el `from .` de arriba y no encuentra
    # estos como modulos sueltos de nivel superior (solo existen asi en
    # tiempo de ejecucion, cuando este archivo corre como script suelto
    # con `terminal/` en sys.path): son el mismo modulo por las dos vias,
    # asi que ignorarlo aqui es correcto y no un error real.
    import ambiente  # type: ignore[no-redef,import-not-found]
    import apuestas  # type: ignore[no-redef,import-not-found]
    import efectos  # type: ignore[no-redef,import-not-found]
    import entrada  # type: ignore[no-redef,import-not-found]
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

# La paleta vive en efectos.py (unico sitio que sabe de codigos ANSI); se
# reexporta aqui porque toda la interfaz la usa en cada linea.
ROJO = efectos.ROJO
VERDE = efectos.VERDE
AMARILLO = efectos.AMARILLO
CELESTE = efectos.CELESTE
GRIS = efectos.GRIS
NEGRITA = efectos.NEGRITA
INVERSO = efectos.INVERSO
RESET = efectos.RESET

# Como se ve cada hueco segun lo que se sabe de el (ver calcular_estados).
# "oculto" solo aparece en el modo oscuridad (ver `oscurecer`).
GLIFOS_ESTADO = {
    "seguro": "✓",
    "peligro": "✗",
    "candidato": "?",
    "probado": "·",
    "oculto": "▒",
}
COLORES_ESTADO = {
    "seguro": VERDE,
    "peligro": ROJO,
    "candidato": AMARILLO,
    "probado": GRIS,
    "oculto": GRIS,
}

# Color de cada linea del panel de acciones recientes, por tipo.
COLORES_ACCION = {
    "disparo": CELESTE,
    "farol": AMARILLO,
    "evento": GRIS,
    "dia": VERDE,
    "aviso": ROJO,
}

# Estados que el modo oscuridad deja ver: solo lo que el jugador ha
# comprobado el mismo. Los candidatos que se deducen de las pistas se
# ocultan; para eso estan las pistas escritas y la memoria.
ESTADOS_VISIBLES_A_OSCURAS = ("seguro", "peligro", "probado")

ANCHO_PANEL = 50
ANCHO_EPILOGO = 62

# Huecos sin probar a partir de los cuales el tambor empieza a latir.
HUECOS_LATIDO = 3

# Vueltas completas que da el resaltado antes de pararse en el hueco
# elegido, al disparar.
VUELTAS_GIRO = 1


if os.name == "nt":
    # Habilita el procesamiento VT100 (codigos ANSI) en cmd.exe moderno:
    # es un efecto secundario documentado de esta llamada "vacia", sin
    # necesitar ninguna dependencia extra (colorama, etc.). Sin esto, en
    # un cmd.exe "clasico" los codigos de color de abajo se verian
    # literales en pantalla en vez de colorear.
    os.system("")


@dataclass
class Tablero:
    """Todo lo que hace falta para pintar el tablero de un turno.

    Se arma de nuevo en cada vuelta del bucle (los estados se recalculan
    a partir de las pistas vigentes); `resaltado` es el unico campo que
    cambia dentro del turno, mientras el selector se mueve por el tambor.
    """

    huecos: int
    estados: dict[int, str]
    pistas_reveladas: list["pistas.Pista"]
    bitacora: "historial.Historial"
    resaltado: int | None = None


def limpiar(duro: bool = False) -> None:
    """Limpia la pantalla (ver efectos.limpiar)."""
    efectos.limpiar(duro)


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


def oscurecer(estados: dict[int, str], huecos: int) -> dict[int, str]:
    """Apaga el tambor: solo sigue viendose lo que se ha comprobado.

    En el modo oscuridad los candidatos que las pistas dejan en pie ya no
    se resaltan y los huecos de los que no se sabe nada se pintan en
    negro: hay que llevar la deduccion en la cabeza, leyendo las pistas,
    y no en los colores del tambor.
    """
    return {
        hueco: (
            estados[hueco]
            if estados.get(hueco) in ESTADOS_VISIBLES_A_OSCURAS
            else "oculto"
        )
        for hueco in range(1, huecos + 1)
    }


def tambor_ascii(
    estados: dict[int, str],
    huecos: int,
    resaltado: int | None = None,
    alerta: bool = False,
) -> str:
    """Monta (sin imprimirlo) el tambor ASCII coloreado segun `estados`.

    Verde = farol acertado ahi, rojo = farol fallido ahi (la bala estuvo
    en ese momento), amarillo = candidato segun las pistas actuales, gris
    = ya disparado o a oscuras. Sin ninguna marca, se muestra sin
    colorear. `resaltado` pinta un hueco en video inverso (el selector de
    flechas y el giro del tambor) y `alerta` tine el marco de rojo (el
    latido de cuando quedan pocos huecos por probar).
    """
    color_marco = f"{NEGRITA}{ROJO}" if alerta else NEGRITA
    superior = f"{color_marco}┌{'───┬' * (huecos - 1)}───┐{RESET}"
    inferior = f"{color_marco}└{'───┴' * (huecos - 1)}───┘{RESET}"
    barra = f"{color_marco}│{RESET}"

    celdas = []
    etiquetas = []
    for hueco in range(1, huecos + 1):
        estado_hueco = estados.get(hueco, "")
        color = COLORES_ESTADO.get(estado_hueco, CELESTE)
        glifo = GLIFOS_ESTADO.get(estado_hueco, "0")
        if hueco == resaltado:
            celdas.append(f"{INVERSO}{NEGRITA} {glifo} {RESET}")
            etiquetas.append(f"{NEGRITA}{AMARILLO}{str(hueco).center(3)}{RESET}")
        else:
            celdas.append(f" {color}{glifo}{RESET} ")
            etiquetas.append(str(hueco).center(3))

    return "\n".join(
        (
            "   " + superior,
            "   " + barra + barra.join(celdas) + barra,
            "   " + inferior,
            "    " + " ".join(etiquetas),
        )
    )


def dibujar_tambor(
    estados: dict[int, str],
    huecos: int,
    resaltado: int | None = None,
    alerta: bool = False,
) -> None:
    """Imprime el tambor ASCII linea a linea (ver `tambor_ascii`)."""
    for linea in tambor_ascii(estados, huecos, resaltado, alerta).split("\n"):
        print(linea)


def panel_acciones(bitacora: "historial.Historial") -> str:
    """Monta el panel inferior con las ultimas acciones de la partida.

    Siempre ocupa el mismo alto (aunque sobren lineas en blanco) para que
    el bloque se pueda repintar en el sitio sin descuadrar la pantalla.
    """
    acciones = bitacora.ultimas_acciones()
    lineas = [f"{GRIS}   ── bitacora ──{RESET}"]
    for accion in acciones:
        color = COLORES_ACCION.get(accion.tipo, GRIS)
        lineas.append(f"   {color}› {accion.texto}{RESET}")
    lineas.extend([""] * (historial.MAX_ACCIONES - len(acciones)))
    return "\n".join(lineas)


def bloque_tablero(tablero: Tablero, alerta: bool = False) -> str:
    """Tambor + panel de acciones: el bloque que se repinta en el sitio.

    Es lo ultimo que dibuja `escena`, asi que las animaciones pueden
    pisarlo subiendo el cursor sin tocar el resto de la pantalla.
    """
    tambor = tambor_ascii(tablero.estados, tablero.huecos, tablero.resaltado, alerta)
    return f"{tambor}\n\n{panel_acciones(tablero.bitacora)}"


def _fila_panel(contenido: str) -> str:
    """Una fila del panel superior, rellenada hasta el ancho fijo.

    El relleno se calcula sobre el ancho visible (sin contar los codigos
    de color), que es lo que descuadraba el marco antes.
    """
    relleno = " " * max(0, ANCHO_PANEL - efectos.ancho_visible(contenido))
    borde = f"{NEGRITA}{CELESTE}║{RESET}"
    return f"{borde}{contenido}{relleno}{borde}"


def cabecera(
    disparos: int,
    apuesta: "apuestas.Apuesta",
    marca: "farol.Farol",
    num_pistas: int = 0,
) -> None:
    """Imprime el panel fijo de la parte de arriba de la pantalla.

    Lleva de un vistazo los cuatro datos que se consultan todo el rato:
    dias de vida, puntos en juego, marcas que quedan y pistas
    acumuladas. Como la pantalla se repinta desde arriba en cada
    fotograma, el panel se queda siempre en el mismo sitio.
    """
    dia = estado.dias_sobrevividos(disparos) + 1
    disparo_del_dia = disparos % estado.DISPAROS_POR_DIA + 1
    marco = f"{NEGRITA}{CELESTE}"

    print(f"{marco}╔{'═' * ANCHO_PANEL}╗{RESET}")
    print(_fila_panel(f"{NEGRITA}{'EL TAMBOR DEL JUICIO'.center(ANCHO_PANEL)}{RESET}"))
    print(f"{marco}╟{'─' * ANCHO_PANEL}╢{RESET}")
    # El dia y las marcas ocupan un campo fijo para que las etiquetas de
    # la derecha caigan en la misma columna en las dos filas; los puntos
    # y las pistas crecen a sus anchas, y el relleno del final absorbe lo
    # que ocupen (el marco solo se descuadraria por encima de mil
    # millones de puntos, que son mas dias de los que da el tambor).
    print(
        _fila_panel(
            f"  Dia {AMARILLO}{dia:<2}{RESET}"
            f" · disparo {disparo_del_dia}/{estado.DISPAROS_POR_DIA}"
            f"    En juego {VERDE}{apuesta.en_juego}{RESET} pts"
        )
    )
    print(
        _fila_panel(
            f"  Marcas {CELESTE}{marca.marcas_restantes:<2}{RESET}"
            f"{' ' * 15}Pistas {AMARILLO}{num_pistas}{RESET}"
        )
    )
    print(f"{marco}╚{'═' * ANCHO_PANEL}╝{RESET}")


def _imprimir_pistas(pistas_reveladas: list["pistas.Pista"]) -> None:
    """Imprime la lista de pistas acumuladas, o el aviso de que aun no
    hay ninguna. Comun a la partida en solitario y al modo duelo."""
    if pistas_reveladas:
        print(NEGRITA + "   Pistas del tambor:" + RESET)
        for indice, pista in enumerate(pistas_reveladas, start=1):
            print(f"   {AMARILLO}#{indice}{RESET} {pista.texto}")
    else:
        print(GRIS + "   La bala descansa en algun hueco. Aun no hay pistas." + RESET)


def escena(
    disparos: int,
    apuesta: "apuestas.Apuesta",
    marca: "farol.Farol",
    tablero: Tablero,
) -> None:
    """Repinta la pantalla entera: panel, pistas y bloque del tablero."""
    limpiar()
    cabecera(disparos, apuesta, marca, len(tablero.pistas_reveladas))
    print()
    _imprimir_pistas(tablero.pistas_reveladas)
    print()
    efectos.pintar_bloque(bloque_tablero(tablero))


def refrescar(dibujar: "partial[None]") -> None:
    """Repinta la escena para borrar el rastro que deja elegir un hueco.

    Ademas de limpiar la linea de ayuda del selector, deja el bloque del
    tablero como lo ultimo pintado, que es lo que necesita el giro para
    animarse en el sitio. Sin animaciones no hay rastro que borrar ni
    giro que preparar, y repetir el tablero solo alargaria el registro.
    """
    if efectos.AJUSTES.animaciones:
        dibujar()


def bala_cerca(marcadas: set[int], huecos: int) -> bool:
    """True cuando quedan pocos huecos sin probar: el tambor se pone tenso."""
    return huecos - len(marcadas) <= HUECOS_LATIDO


def latido(tablero: Tablero, pulsos: int = 3) -> None:
    """Hace latir el tambor en rojo, cada vez mas rapido.

    Se llama justo despues de `escena`, que deja el bloque del tablero
    como lo ultimo pintado; el ultimo fotograma es el normal, para que la
    pantalla quede en reposo al terminar.
    """
    normal = bloque_tablero(tablero)
    alerta = bloque_tablero(tablero, alerta=True)
    fotogramas = [alerta, normal] * pulsos
    efectos.repintar(fotogramas, retardo=0.26, factor=0.72)


def _secuencia_giro(
    huecos: int, destino: int, vueltas: int = VUELTAS_GIRO
) -> list[int]:
    """Huecos por los que pasa el resaltado hasta pararse en `destino`."""
    total = vueltas * huecos + destino
    return [indice % huecos + 1 for indice in range(total)]


def animar_giro(tablero: Tablero, destino: int) -> None:
    """Gira el tambor y lo para en `destino`, frenando poco a poco."""
    resaltado_previo = tablero.resaltado
    fotogramas = []
    for hueco in _secuencia_giro(tablero.huecos, destino):
        tablero.resaltado = hueco
        fotogramas.append(bloque_tablero(tablero))
    tablero.resaltado = resaltado_previo
    efectos.beep("clic")
    efectos.repintar(fotogramas, retardo=0.035, factor=1.13)


def elegir_accion(marcas_restantes: int) -> str:
    """Pide al jugador si dispara, se retira o (si le quedan) marca."""
    if marcas_restantes > 0:
        opciones = f"(D)isparar, (R)etirarse o (M)arcar [{marcas_restantes}]"
    else:
        opciones = "(D)isparar o (R)etirarse"
    while True:
        entrada_leida = input(f"{NEGRITA}   {opciones}: {RESET}").strip().lower()
        if entrada_leida in ("d", "disparar"):
            return "disparar"
        if entrada_leida in ("r", "retirarse"):
            return "retirarse"
        if marcas_restantes > 0 and entrada_leida in ("m", "marcar"):
            return "marcar"
        print(ROJO + "   Esa respuesta no esta entre las opciones." + RESET)


def elegir_posicion(huecos: int) -> int:
    """Pide al jugador una posicion valida del tambor, tecleada."""
    while True:
        leido = input(f"{NEGRITA}   Elige una posicion (1-{huecos}): {RESET}").strip()
        try:
            posicion = int(leido)
        except ValueError:
            print(ROJO + "   Eso no parece un numero." + RESET)
            continue
        if posicion < 1 or posicion > huecos:
            print(ROJO + "   Ese numero no esta en el tambor." + RESET)
            continue
        return posicion


def elegir_hueco(tablero: Tablero, dibujar: "partial[None]", verbo: str) -> int | None:
    """Elige un hueco recorriendo el tambor con las flechas.

    En una terminal de verdad se navega con ← y → y se confirma con
    Enter (Esc o Q se echan atras y devuelven None). Donde no se puede
    leer tecla a tecla -- un pipe, los tests, CI -- se cae al metodo de
    siempre: teclear el numero, que nunca cancela.
    """
    if not entrada.modo_tecla_disponible():
        return elegir_posicion(tablero.huecos)

    def pintar(seleccion: int) -> None:
        tablero.resaltado = seleccion
        dibujar()
        print(
            f"{NEGRITA}   {verbo} el hueco {AMARILLO}{seleccion}{RESET}"
            f"{GRIS}   ← → mueven · Enter confirma · Esc cancela{RESET}"
        )

    try:
        return entrada.seleccionar(tablero.huecos, pintar)
    finally:
        tablero.resaltado = None


def amanecer(dia: int, bitacora: "historial.Historial") -> None:
    """Abre un dia nuevo con una frase de ambiente, tecleada despacio."""
    texto = ambiente.mensaje_de_dia(dia)
    bitacora.registrar_accion("dia", f"Amanece el dia {dia}.")
    print()
    efectos.escribir(f"   {GRIS}{texto}{RESET}")
    efectos.pausa(1.2)


def cartel_evento(evento: str) -> None:
    """Planta el cartel a pantalla completa de un evento del tambor."""
    efectos.beep("zumbido" if evento == "tambor_caliente" else "clic")
    efectos.banner(
        ambiente.cartel_evento(evento, eventos.texto_de(evento)),
        color=AMARILLO,
        segundos=2.0,
    )


def revelar_pista(numero: int, pista: "pistas.Pista") -> None:
    """Imprime una pista recien salida con efecto de teletipo."""
    efectos.escribir(f"   {AMARILLO}#{numero}{RESET} {pista.texto}")


def _imprimir_epilogo(final: "ambiente.Epilogo", color: str) -> None:
    """Imprime el titulo y el parrafo del final que cierra la partida."""
    print()
    print(f"{NEGRITA}{color}   ── {final.titulo} ──{RESET}")
    for linea in textwrap.wrap(final.texto, width=ANCHO_EPILOGO):
        print(f"{GRIS}   {linea}{RESET}")


def impacto(
    disparos: int,
    perdidos: int,
    dias: int,
    resumen_texto: str,
    nuevo_record: bool = False,
    final: "ambiente.Epilogo | None" = None,
) -> None:
    """Muestra la pantalla de derrota (BOOM), lo perdido y el epilogo."""
    limpiar()
    efectos.beep("impacto")
    print()
    for linea in ambiente.ARTE_BOOM:
        print(f"{NEGRITA}{ROJO}   {linea}{RESET}")
    print(f"{ROJO}   {'B O O M'.center(36)}{RESET}")
    print()
    print(ROJO + "   La bala ha encontrado tu numero." + RESET)
    print(
        f"{AMARILLO}   Caiste tras {disparos} disparo(s) ({dias} dia(s) "
        f"sobrevivido(s)), perdiendo {perdidos} puntos.{RESET}"
    )
    if nuevo_record:
        print(NEGRITA + AMARILLO + "   ¡Nuevo record de dias sobrevividos!" + RESET)
    print(f"{CELESTE}   {resumen_texto}{RESET}")
    _imprimir_epilogo(final or ambiente.epilogo(dias, retirado=False), ROJO)
    print()
    efectos.pausa(2.5)


def retirada(
    disparos: int,
    ganados: int,
    dias: int,
    resumen_texto: str,
    nuevo_record: bool = False,
    final: "ambiente.Epilogo | None" = None,
) -> None:
    """Muestra la pantalla de retirada, lo cobrado y el epilogo."""
    limpiar()
    efectos.beep("acierto")
    print(NEGRITA + VERDE + "\n    ✦  TE RETIRAS A TIEMPO  ✦\n" + RESET)
    print(
        f"{CELESTE}   Cobras {ganados} puntos tras {disparos} disparo(s) "
        f"({dias} dia(s) sobrevivido(s)).{RESET}"
    )
    if nuevo_record:
        print(NEGRITA + AMARILLO + "   ¡Nuevo record de dias sobrevividos!" + RESET)
    print(f"{VERDE}   {resumen_texto}{RESET}")
    _imprimir_epilogo(
        final or ambiente.epilogo(dias, retirado=True, puntos=ganados), VERDE
    )
    print()
    efectos.pausa(2.5)


def _resolver_farol(
    posicion: int,
    tambor: "estado.TamborJuicio",
    marca: "farol.Farol",
    apuesta: "apuestas.Apuesta",
    bitacora: "historial.Historial",
    resultados_farol: dict[int, str],
) -> None:
    """Gasta una marca en `posicion` y cuenta como ha ido.

    Comun a la partida en solitario y al duelo: solo cambia de quien son
    la marca, la apuesta y la bitacora que se le pasan.
    """
    acierto = marca.marcar(posicion, tambor.posicion_bala)
    bitacora.registrar_farol(acierto)
    resultados_farol[posicion] = "seguro" if acierto else "peligro"
    if acierto:
        apuesta.sumar_bono(BONO_MARCA_ACERTADA)
        bitacora.registrar_accion(
            "farol", f"Farol en el {posicion}: vacio (+{BONO_MARCA_ACERTADA} pts)"
        )
        efectos.beep("acierto")
        print(
            f"{VERDE}   Farol acertado: el hueco {posicion} estaba "
            f"vacio. +{BONO_MARCA_ACERTADA} puntos.{RESET}"
        )
    else:
        bitacora.registrar_accion("aviso", f"Farol en el {posicion}: ahi estaba")
        efectos.beep("fallo")
        print(f"{ROJO}   Farol fallido: ahi estaba la bala. Pierdes la marca.{RESET}")
    efectos.pausa(1.5)


def _resolver_evento(
    tambor: "estado.TamborJuicio", bitacora: "historial.Historial"
) -> str | None:
    """Sortea un evento, lo aplica y lo anuncia con su cartel.

    Devuelve el evento (o None) para que quien llama sepa si la proxima
    pista sale mentirosa.
    """
    evento = eventos.tirar_evento()
    if evento is None:
        return None
    if evento == "clic_metalico":
        tambor.mover_extra()
    bitacora.registrar_evento(evento)
    bitacora.registrar_accion("evento", evento.replace("_", " ").capitalize())
    cartel_evento(evento)
    return evento


def jugar(
    huecos: int = estado.HUECOS,
    marcas: int = farol.MARCAS_INICIALES,
    oscuridad: bool = False,
) -> None:
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

        limpiar(duro=True)
        amanecer(1, bitacora)

        while True:
            candidatos = pistas.interseccion(pistas_reveladas)
            estados = calcular_estados(marcadas, resultados_farol, candidatos)
            if oscuridad:
                estados = oscurecer(estados, tambor.huecos)
            tablero = Tablero(tambor.huecos, estados, pistas_reveladas, bitacora)
            dibujar = partial(escena, disparos, apuesta, marca, tablero)

            dibujar()
            if bala_cerca(marcadas, tambor.huecos):
                latido(tablero)
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
                    ambiente.epilogo(
                        dias,
                        retirado=True,
                        faroles_usados=bitacora.faroles_usados,
                        faroles_acertados=bitacora.faroles_acertados,
                        puntos=ganados,
                    ),
                )
                break

            if accion == "marcar":
                posicion = elegir_hueco(tablero, dibujar, "Marcar")
                if posicion is None:
                    continue
                refrescar(dibujar)
                _resolver_farol(
                    posicion, tambor, marca, apuesta, bitacora, resultados_farol
                )
                continue

            posicion = elegir_hueco(tablero, dibujar, "Disparar a")
            if posicion is None:
                continue
            refrescar(dibujar)
            animar_giro(tablero, posicion)
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
                    ambiente.epilogo(
                        dias,
                        retirado=False,
                        faroles_usados=bitacora.faroles_usados,
                        faroles_acertados=bitacora.faroles_acertados,
                        puntos=perdidos,
                    ),
                )
                break

            apuesta.doblar()
            efectos.beep("fallo")
            bitacora.registrar_accion(
                "disparo", f"Disparo al {posicion}: vacio ({apuesta.en_juego} pts)"
            )
            evento = _resolver_evento(tambor, bitacora)

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
            revelar_pista(len(pistas_reveladas), pistas_reveladas[-1])
            if disparos % estado.DISPAROS_POR_DIA == 0:
                dia_nuevo = estado.dias_sobrevividos(disparos)
                print(f"{AMARILLO}   Sobrevives al dia {dia_nuevo}.{RESET}")
                amanecer(dia_nuevo + 1, bitacora)
            efectos.pausa(1.5)

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
    leido = input(f"{NEGRITA}   {prefijo}{RESET}").strip()
    return leido or f"Jugador {numero}"


def escena_duelo(
    activo: JugadorDuelo,
    rival: JugadorDuelo,
    tablero: Tablero,
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
    cabecera(
        activo.disparos, activo.apuesta, activo.marca, len(tablero.pistas_reveladas)
    )
    print()
    _imprimir_pistas(tablero.pistas_reveladas)
    print()
    efectos.pintar_bloque(bloque_tablero(tablero))


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
    efectos.pausa(1)
    input(NEGRITA + "   Pulsa Enter para continuar..." + RESET)


def jugar_duelo(
    huecos: int = estado.HUECOS,
    marcas: int = farol.MARCAS_INICIALES,
    oscuridad: bool = False,
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

    limpiar(duro=True)
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
            if oscuridad:
                estados = oscurecer(estados, tambor.huecos)
            tablero = Tablero(tambor.huecos, estados, pistas_reveladas, activo.bitacora)
            dibujar = partial(escena_duelo, activo, rival, tablero)

            dibujar()
            if bala_cerca(marcadas, tambor.huecos):
                latido(tablero)
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
                    ambiente.epilogo(
                        activo.dias,
                        retirado=True,
                        faroles_usados=activo.bitacora.faroles_usados,
                        faroles_acertados=activo.bitacora.faroles_acertados,
                        puntos=activo.puntos_finales,
                    ),
                )
                break

            if accion == "marcar":
                posicion = elegir_hueco(tablero, dibujar, "Marcar")
                if posicion is None:
                    continue
                refrescar(dibujar)
                _resolver_farol(
                    posicion,
                    tambor,
                    activo.marca,
                    activo.apuesta,
                    activo.bitacora,
                    resultados_farol,
                )
                turno += 1
                continue

            posicion = elegir_hueco(tablero, dibujar, "Disparar a")
            if posicion is None:
                continue
            refrescar(dibujar)
            animar_giro(tablero, posicion)
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
                    ambiente.epilogo(
                        activo.dias,
                        retirado=False,
                        faroles_usados=activo.bitacora.faroles_usados,
                        faroles_acertados=activo.bitacora.faroles_acertados,
                        puntos=activo.puntos_finales,
                    ),
                )
                break

            activo.apuesta.doblar()
            efectos.beep("fallo")
            activo.bitacora.registrar_accion(
                "disparo",
                f"Disparo al {posicion}: vacio ({activo.apuesta.en_juego} pts)",
            )
            evento = _resolver_evento(tambor, activo.bitacora)

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
            revelar_pista(len(pistas_reveladas), pistas_reveladas[-1])
            efectos.pausa(1.5)
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
        "--oscuridad",
        action="store_true",
        help="Modo a oscuras: el tambor solo muestra lo que ya has comprobado.",
    )
    parser.add_argument(
        "--sin-animaciones",
        action="store_true",
        help="Sin giros, latidos ni pausas: la partida como un registro (util en CI).",
    )
    parser.add_argument(
        "--sin-sonido",
        action="store_true",
        help="Silencia el timbre de la terminal.",
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

    efectos.configurar(animaciones=not args.sin_animaciones, sonido=not args.sin_sonido)

    try:
        if args.duelo:
            jugar_duelo(
                huecos=args.huecos, marcas=args.marcas, oscuridad=args.oscuridad
            )
        else:
            jugar(huecos=args.huecos, marcas=args.marcas, oscuridad=args.oscuridad)
    except KeyboardInterrupt:
        print()
        print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)
    finally:
        efectos.cursor(True)


if __name__ == "__main__":
    main()
