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
import random
import sys
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
        jugador,
        motor,
        pistas,
        records,
        semillas,
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
    import jugador  # type: ignore[no-redef,import-not-found]
    import motor  # type: ignore[no-redef,import-not-found]
    import pistas  # type: ignore[no-redef,import-not-found]
    import records  # type: ignore[no-redef,import-not-found]
    import semillas  # type: ignore[no-redef,import-not-found]

# Reglas del juego: viven en motor.py. Se reexportan aqui porque la
# cabecera las enseña en pantalla, porque terminal/paridad.py las lee de
# este modulo y porque quien ya las importaba de ruleta no tiene por que
# enterarse de la mudanza.
APUESTA_BASE = motor.APUESTA_BASE
BONO_MARCA_ACERTADA = motor.BONO_MARCA_ACERTADA

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
    barra = f"{color_marco}│{RESET}"

    # Cada hueco ocupa 4 columnas (3 de celda + el separador) y la fila
    # arrastra un margen de 3 mas el borde de cierre. Con muchos huecos
    # el tambor no cabe de una pieza y se parte en varias filas: antes
    # salia en una sola linea que la terminal partia por su cuenta, y eso
    # descuadraba la pantalla entera, porque la escena se repinta con
    # posicionamiento absoluto contando las lineas que ocupa.
    por_fila = max(1, (efectos.ancho_terminal() - 4) // 4)

    lineas: list[str] = []
    for inicio in range(0, huecos, por_fila):
        tramo = range(inicio + 1, min(inicio + por_fila, huecos) + 1)
        celdas = []
        etiquetas = []
        for hueco in tramo:
            estado_hueco = estados.get(hueco, "")
            color = COLORES_ESTADO.get(estado_hueco, CELESTE)
            glifo = GLIFOS_ESTADO.get(estado_hueco, "0")
            if hueco == resaltado:
                # Los corchetes, y no solo el video inverso, son lo que
                # hace visible el hueco elegido cuando no hay color
                # (--sin-color, NO_COLOR, salida a un fichero): sin ellos
                # la celda resaltada quedaba exactamente igual que las
                # demas y el selector se volvia invisible.
                celdas.append(f"{INVERSO}{NEGRITA}[{glifo}]{RESET}")
                etiquetas.append(f"{NEGRITA}{AMARILLO}{str(hueco).center(3)}{RESET}")
            else:
                celdas.append(f" {color}{glifo}{RESET} ")
                etiquetas.append(str(hueco).center(3))

        marco = "┬".join(["───"] * len(tramo))
        lineas.extend(
            (
                "   " + f"{color_marco}┌{marco}┐{RESET}",
                "   " + barra + barra.join(celdas) + barra,
                "   " + f"{color_marco}└{marco.replace('┬', '┴')}┘{RESET}",
                "    " + " ".join(etiquetas),
            )
        )

    return "\n".join(lineas)


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


def amanecer(
    dia: int,
    bitacora: "historial.Historial",
    azar: "random.Random | None" = None,
) -> None:
    """Abre un dia nuevo con una frase de ambiente, tecleada despacio."""
    texto = ambiente.mensaje_de_dia(dia, rng=azar)
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


def sello_semilla(valor: int) -> None:
    """Deja escrita la semilla de la partida que acaba de terminar.

    Se imprime DESPUES de impacto()/retirada() y no dentro: esas dos
    pantallas son la parte narrativa del cierre, y el numero con el que
    repetir la partida es una nota al pie que no pinta nada dentro del
    epilogo.
    """
    print(f"{GRIS}   Semilla de esta partida: {valor}{RESET}")
    print(f"{GRIS}   Repitela tal cual con:  --seed {valor}{RESET}")
    print()


def _pedir_nombre(numero: int) -> str:
    """Pide el nombre de un jugador; en blanco usa 'Jugador N'."""
    prefijo = f"Nombre del jugador {numero} (Enter para 'Jugador {numero}'): "
    leido = input(f"{NEGRITA}   {prefijo}{RESET}").strip()
    return leido or f"Jugador {numero}"


def escena_duelo(
    activo: "jugador.Jugador",
    rival: "jugador.Jugador",
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


def resultado_duelo(jugadores: list["jugador.Jugador"]) -> None:
    """Compara a los jugadores (dias sobrevividos y, en caso de empate,
    puntos alcanzados) y muestra quien gana el duelo."""
    limpiar()
    print(NEGRITA + AMARILLO + "\n   === RESULTADO DEL DUELO ===\n" + RESET)
    for uno in jugadores:
        print(
            f"   {uno.nombre}: {uno.dias} dia(s) sobrevividos, "
            f"{uno.puntos_finales} puntos."
        )
    print()

    finalistas = jugador.ganadores(jugadores)
    if len(finalistas) > 1:
        print(NEGRITA + CELESTE + "   Empate. El tambor no se decide." + RESET)
    else:
        print(NEGRITA + VERDE + f"   ¡Gana {finalistas[0].nombre}!" + RESET)
    print()
    efectos.pausa(1)
    input(NEGRITA + "   Pulsa Enter para continuar..." + RESET)


@dataclass
class Partida:
    """Lo que la interfaz necesita recordar de la partida que esta pintando.

    El motor ya lleva las reglas; esto es lo que solo importa en pantalla:
    como pintar cada hueco faroleado, si hay que anunciar un dia nuevo y
    si la partida ya termino de contarse.
    """

    juego: "motor.Motor"
    misrecords: "records.Records"
    resultados_farol: dict[int, str] = field(default_factory=dict)

    # Quien acaba de actuar. NO es lo mismo que `juego.jugador_activo`:
    # el motor pasa el turno antes de devolver los sucesos, asi que para
    # cuando esto se pinta el activo ya es el otro. En un duelo eso
    # escribia el "Disparo al 3: vacio" en la bitacora del rival.
    actor: "jugador.Jugador | None" = None


def _contar_suceso(suceso: "motor.Suceso", partida: Partida) -> None:
    """Pinta en pantalla una cosa que acaba de pasar en la partida.

    Un caso por cada suceso que devuelve el motor, en el mismo orden en
    que los devuelve: aqui no se decide nada del juego, solo como se
    cuenta. Ver motor.py para que significa cada uno.
    """
    juego = partida.juego
    bitacora = partida.actor.bitacora if partida.actor else juego.bitacora

    if isinstance(suceso, motor.EntradaInvalida):
        print(ROJO + "   Ese numero no esta en el tambor." + RESET)
        return

    if isinstance(suceso, motor.EventoTambor):
        bitacora.registrar_accion("evento", suceso.tipo.replace("_", " ").capitalize())
        cartel_evento(suceso.tipo)
        return

    if isinstance(suceso, motor.DisparoSobrevivido):
        efectos.beep("fallo")
        bitacora.registrar_accion(
            "disparo",
            f"Disparo al {juego.tambor.ultimo_disparo}: vacio ({suceso.en_juego} pts)",
        )
        print(
            f"{VERDE}   Click. Cartucho vacio. Lo apostado se dobla "
            f"a {suceso.en_juego} puntos.{RESET}"
        )
        return

    if isinstance(suceso, motor.PistaNueva):
        revelar_pista(suceso.numero, suceso.pista)
        return

    if isinstance(suceso, motor.DiaCompletado):
        # El duelo no anuncia dias ni amanece: cada jugador lleva los
        # suyos, y un amanecer compartido a mitad del turno del otro no
        # cuadraria. Se conserva tal cual estaba antes de unificar los
        # dos bucles -- aunque los dias sean justo lo que decide quien
        # gana un duelo, y anunciarlos ahi tenga su logica: eso es un
        # cambio de juego y no entra en un commit que mueve codigo.
        if juego.es_duelo():
            return
        print(f"{AMARILLO}   Sobrevives al dia {suceso.dia}.{RESET}")
        amanecer(suceso.dia + 1, bitacora, juego.azar)
        return

    if isinstance(suceso, motor.FarolResuelto):
        partida.resultados_farol[suceso.hueco] = (
            "seguro" if suceso.acierto else "peligro"
        )
        if suceso.acierto:
            bitacora.registrar_accion(
                "farol", f"Farol en el {suceso.hueco}: vacio (+{suceso.bono} pts)"
            )
            efectos.beep("acierto")
            print(
                f"{VERDE}   Farol acertado: el hueco {suceso.hueco} estaba "
                f"vacio. +{suceso.bono} puntos.{RESET}"
            )
        else:
            bitacora.registrar_accion(
                "aviso", f"Farol en el {suceso.hueco}: ahi estaba"
            )
            efectos.beep("fallo")
            print(
                f"{ROJO}   Farol fallido: ahi estaba la bala. "
                f"Pierdes la marca.{RESET}"
            )
        efectos.pausa(1.5)
        return

    if isinstance(suceso, motor.Impacto | motor.Retirada):
        _cerrar_partida(suceso, partida)
        return

    if isinstance(suceso, motor.TurnoCambiado):
        return

    if isinstance(suceso, motor.DueloTerminado):
        resultado_duelo(suceso.jugadores)


def _cerrar_partida(final: "motor.Impacto | motor.Retirada", partida: Partida) -> None:
    """Apunta el resultado en los records y saca la pantalla de cierre.

    Los records los lleva la interfaz y no el motor, igual que en la
    version de Godot: el motor no toca disco. El "nuevo record" se mira
    ANTES de registrar la partida, porque registrarla ya sube el maximo.
    """
    bitacora = partida.actor.bitacora if partida.actor else partida.juego.bitacora
    muerto = isinstance(final, motor.Impacto)
    puntos = final.perdidos if isinstance(final, motor.Impacto) else final.ganados

    nuevo_record = final.dias > partida.misrecords.dias_maximos
    partida.misrecords.registrar_partida(
        final.dias, puntos, bitacora.faroles_usados, bitacora.faroles_acertados
    )
    records.guardar(partida.misrecords)

    epilogo = ambiente.epilogo(
        final.dias,
        retirado=not muerto,
        faroles_usados=bitacora.faroles_usados,
        faroles_acertados=bitacora.faroles_acertados,
        puntos=puntos,
    )
    pantalla = impacto if muerto else retirada
    pantalla(
        final.disparos,
        puntos,
        final.dias,
        historial.resumen(bitacora, final.dias),
        nuevo_record,
        epilogo,
    )


def _pintar_turno(partida: Partida, oscuridad: bool) -> tuple[Tablero, "partial[None]"]:
    """Arma el tablero del turno y devuelve con que repintarlo.

    Se rehace en cada vuelta porque los estados se recalculan a partir
    de las pistas vigentes, que cambian con cada disparo.
    """
    juego = partida.juego
    estados = calcular_estados(
        juego.marcadas(), partida.resultados_farol, juego.candidatos()
    )
    if oscuridad:
        estados = oscurecer(estados, juego.huecos)
    tablero = Tablero(juego.huecos, estados, juego.pistas_reveladas, juego.bitacora)

    if juego.es_duelo():
        rival = juego.jugadores[(juego.turno + 1) % len(juego.jugadores)]
        return tablero, partial(escena_duelo, juego.jugador_activo, rival, tablero)
    return tablero, partial(escena, juego.disparos, juego.apuesta, juego.marca, tablero)


def jugar(
    huecos: int = estado.HUECOS,
    marcas: int = farol.MARCAS_INICIALES,
    oscuridad: bool = False,
    duelo: bool = False,
    seed: int | None = None,
) -> None:
    """Ejecuta el bucle principal: disparar, marcar o retirarse.

    Es el mismo bucle para los dos modos. Una partida en solitario es un
    duelo de un unico jugador (ver motor.py y jugador.py), asi que lo
    unico que cambia con `duelo=True` es que hay dos nombres, que el
    tablero se pinta con el turno y el rival encima, y que al final se
    compara quien gano: las reglas son las mismas y solo estan escritas
    una vez.

    `seed` fija la primera partida de la sesion; las siguientes sortean
    la suya y la enseñan al terminar (ver semillas.py). Cada partida
    tiene su generador, asi que dos sesiones que arranquen con la misma
    semilla juegan la misma primera partida aunque se pulsen teclas
    distintas por el camino: el azar no depende de cuantas veces se haya
    repintado la pantalla.
    """
    misrecords = records.cargar()
    pendiente = seed

    nombres: list[str] = []
    if duelo:
        limpiar(duro=True)
        print(NEGRITA + CELESTE + "\n   === EL TAMBOR DEL JUICIO: DUELO ===\n" + RESET)
        nombres = [_pedir_nombre(1), _pedir_nombre(2)]

    while True:
        pedida = pendiente is not None
        semilla_partida = pendiente if pendiente is not None else semillas.nueva()
        pendiente = None
        partida = Partida(
            motor.Motor(
                huecos=huecos,
                marcas=marcas,
                nombres=nombres,
                rng=semillas.generador(semilla_partida),
            ),
            misrecords,
        )
        juego = partida.juego

        limpiar(duro=True)
        if not duelo:
            amanecer(1, juego.bitacora, juego.azar)
        if pedida:
            # Solo cuando el jugador la pidio: quien juega normal no
            # necesita ver un numero de diez cifras antes de empezar,
            # pero quien viene a repetir una partida (o a reproducir un
            # fallo) si quiere confirmar que arranco la que pidio.
            print(f"{GRIS}   Semilla: {semilla_partida}{RESET}")

        while not juego.terminada:
            tablero, dibujar = _pintar_turno(partida, oscuridad)
            dibujar()
            if bala_cerca(juego.marcadas(), juego.huecos):
                latido(tablero)

            accion = elegir_accion(juego.marca.marcas_restantes)
            # Se apunta antes de actuar: despues, el turno ya ha pasado.
            partida.actor = juego.jugador_activo
            if accion == "retirarse":
                sucesos = juego.retirarse()
            else:
                verbo = "Marcar" if accion == "marcar" else "Disparar a"
                posicion = elegir_hueco(tablero, dibujar, verbo)
                if posicion is None:
                    continue
                refrescar(dibujar)
                if accion == "marcar":
                    sucesos = juego.marcar(posicion)
                else:
                    animar_giro(tablero, posicion)
                    sucesos = juego.disparar(posicion)

            for suceso in sucesos:
                _contar_suceso(suceso, partida)
            if accion == "disparar" and not juego.terminada:
                efectos.pausa(1.5)

        sello_semilla(semilla_partida)
        pregunta = (
            "Jugar otro duelo? (s/n): " if duelo else "Jugar otra partida? (s/n): "
        )
        otra = input(NEGRITA + f"   {pregunta}" + RESET).strip().lower()
        if otra not in ("s", "si", "y", "yes"):
            print(f"{AMARILLO}   Hasta la proxima. El tambor siempre espera.{RESET}")
            break


def _version_texto() -> str:
    """Version del paquete instalado (la que declara pyproject.toml), o
    un aviso claro si se ejecuta el script directamente sin instalar (no
    hay metadata de paquete que leer en ese caso: PackageNotFoundError).
    """
    try:
        return version("tambor-del-juicio")
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
        "--seed",
        type=int,
        default=None,
        help=(
            "Repite una partida concreta: mismo tambor, mismas pistas y "
            "mismos eventos. Cada partida imprime la suya al terminar."
        ),
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
        "--sin-color",
        action="store_true",
        help=(
            "Sin codigos de color. Tambien se apagan solos con NO_COLOR "
            "en el entorno o si la salida no es una terminal."
        ),
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


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada real del juego (usado por `run.sh`/`run.bat` via
    `__main__` y por el comando `ruleta` instalable via pyproject.toml):
    envuelve jugar() para que Ctrl+C siempre salga con el mensaje de
    despedida en vez de un traceback. `argv=None` hace que argparse lea
    sys.argv real (comportamiento normal); se le puede pasar una lista
    para lanzar el juego con otros parametros sin pasar por la terminal.

    Devuelve el codigo de salida del proceso, que es lo que espera tanto
    el `sys.exit(main())` de aqui abajo como el comando `ruleta` que
    genera setuptools: antes no devolvia nada, asi que el juego salia
    siempre con 0 y un `ruleta && algo` encadenaba aunque el jugador
    hubiera abortado con Ctrl+C.
    """
    # Lo primero de todo: sin esto, en Windows con la salida redirigida
    # (cp1252) el primer caracter de marco aborta la partida.
    efectos.asegurar_utf8()

    args = _parsear_args(argv)

    if args.records:
        print(records.resumen(records.cargar()))
        return 0

    efectos.configurar(animaciones=not args.sin_animaciones, sonido=not args.sin_sonido)
    # El filtro va sobre sys.stdout, asi que se instala antes de la
    # primera linea de juego y se quita en el finally: dejarlo puesto
    # ensuciaria la salida de quien importe este modulo en vez de
    # ejecutarlo.
    efectos.filtrar_color(not efectos.color_activo(sin_color=args.sin_color))

    try:
        jugar(
            huecos=args.huecos,
            marcas=args.marcas,
            oscuridad=args.oscuridad,
            duelo=args.duelo,
            seed=args.seed,
        )
    except (KeyboardInterrupt, EOFError) as interrupcion:
        # EOFError ademas de KeyboardInterrupt: el juego se apoya en
        # input() en seis sitios (la accion del turno, la posicion, el
        # farol, las dos preguntas de "otra partida?" y la pausa entre
        # pantallas), y todos lo lanzan cuando ya no queda entrada que
        # leer: Ctrl+D, o stdin redirigido y agotado (`echo | ruleta`,
        # un script que alimente la partida, un run de CI). Sin
        # capturarlo, cualquiera de esos casos terminaba escupiendo un
        # traceback de EOFError en vez de la despedida.
        print()
        print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)
        # Ctrl+C es una interrupcion de verdad, y la convencion del shell
        # para eso es 128+SIGINT = 130; quedarse sin entrada (Ctrl+D, un
        # pipe agotado) no es ningun fallo, solo el final de la partida.
        return 130 if isinstance(interrupcion, KeyboardInterrupt) else 0
    finally:
        efectos.cursor(True)
        efectos.filtrar_color(False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
