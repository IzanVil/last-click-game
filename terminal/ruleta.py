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
        rival,
        semillas,
    )
except ImportError:  # pragma: no cover
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
    import rival  # type: ignore[no-redef,import-not-found]
    import semillas  # type: ignore[no-redef,import-not-found]

APUESTA_BASE = motor.APUESTA_BASE
BONO_MARCA_ACERTADA = motor.BONO_MARCA_ACERTADA

DIFICULTADES = {
    "facil": {"huecos": 10, "marcas": 4},
    "normal": {"huecos": estado.HUECOS, "marcas": farol.MARCAS_INICIALES},
    "dificil": {"huecos": 6, "marcas": 2},
}

ROJO = efectos.ROJO
VERDE = efectos.VERDE
AMARILLO = efectos.AMARILLO
CELESTE = efectos.CELESTE
GRIS = efectos.GRIS
NEGRITA = efectos.NEGRITA
INVERSO = efectos.INVERSO
RESET = efectos.RESET

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

COLORES_ACCION = {
    "disparo": CELESTE,
    "farol": AMARILLO,
    "evento": GRIS,
    "dia": VERDE,
    "aviso": ROJO,
}

ESTADOS_VISIBLES_A_OSCURAS = ("seguro", "peligro", "probado")

ANCHO_PANEL = 50
ANCHO_EPILOGO = 62

HUECOS_LATIDO = 3

VUELTAS_GIRO = 1


if os.name == "nt":
    os.system("")


@dataclass
class Tablero:
    huecos: int
    estados: dict[int, str]
    pistas_reveladas: list["pistas.Pista"]
    bitacora: "historial.Historial"
    resaltado: int | None = None


def limpiar(duro: bool = False) -> None:
    efectos.limpiar(duro)


def calcular_estados(
    marcadas: set[int], resultados_farol: dict[int, str], candidatos: frozenset[int]
) -> dict[int, str]:
    estados: dict[int, str] = {hueco: "candidato" for hueco in candidatos}
    for hueco in marcadas:
        estados[hueco] = "probado"
    estados.update(resultados_farol)
    return estados


def oscurecer(estados: dict[int, str], huecos: int) -> dict[int, str]:
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
    color_marco = f"{NEGRITA}{ROJO}" if alerta else NEGRITA
    barra = f"{color_marco}│{RESET}"

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
    for linea in tambor_ascii(estados, huecos, resaltado, alerta).split("\n"):
        print(linea)


def panel_acciones(bitacora: "historial.Historial") -> str:
    acciones = bitacora.ultimas_acciones()
    lineas = [f"{GRIS}   ── bitacora ──{RESET}"]
    for accion in acciones:
        color = COLORES_ACCION.get(accion.tipo, GRIS)
        lineas.append(f"   {color}› {accion.texto}{RESET}")
    lineas.extend([""] * (historial.MAX_ACCIONES - len(acciones)))
    return "\n".join(lineas)


def bloque_tablero(tablero: Tablero, alerta: bool = False) -> str:
    tambor = tambor_ascii(tablero.estados, tablero.huecos, tablero.resaltado, alerta)
    return f"{tambor}\n\n{panel_acciones(tablero.bitacora)}"


def _fila_panel(contenido: str) -> str:
    relleno = " " * max(0, ANCHO_PANEL - efectos.ancho_visible(contenido))
    borde = f"{NEGRITA}{CELESTE}║{RESET}"
    return f"{borde}{contenido}{relleno}{borde}"


def cabecera(
    disparos: int,
    apuesta: "apuestas.Apuesta",
    marca: "farol.Farol",
    num_pistas: int = 0,
) -> None:
    dia = estado.dias_sobrevividos(disparos) + 1
    disparo_del_dia = disparos % estado.DISPAROS_POR_DIA + 1
    marco = f"{NEGRITA}{CELESTE}"

    print(f"{marco}╔{'═' * ANCHO_PANEL}╗{RESET}")
    print(_fila_panel(f"{NEGRITA}{'EL TAMBOR DEL JUICIO'.center(ANCHO_PANEL)}{RESET}"))
    print(f"{marco}╟{'─' * ANCHO_PANEL}╢{RESET}")
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
    if pistas_reveladas:
        print(NEGRITA + "   Pistas del tambor:" + RESET)
        for indice, pista in enumerate(pistas_reveladas, start=1):
            print(f"   {AMARILLO}#{indice}{RESET} {pista.texto}")
    else:
        print(GRIS + "   La bala descansa en algun hueco. Aun no hay pistas." + RESET)


def _cuerpo_de_escena(
    disparos: int,
    apuesta: "apuestas.Apuesta",
    marca: "farol.Farol",
    tablero: Tablero,
) -> None:
    cabecera(disparos, apuesta, marca, len(tablero.pistas_reveladas))
    print()
    _imprimir_pistas(tablero.pistas_reveladas)
    print()
    efectos.pintar_bloque(bloque_tablero(tablero))


def escena(
    disparos: int,
    apuesta: "apuestas.Apuesta",
    marca: "farol.Farol",
    tablero: Tablero,
) -> None:
    limpiar()
    _cuerpo_de_escena(disparos, apuesta, marca, tablero)


def refrescar(dibujar: "partial[None]") -> None:
    if efectos.AJUSTES.animaciones:
        dibujar()


def bala_cerca(marcadas: set[int], huecos: int) -> bool:
    return huecos - len(marcadas) <= HUECOS_LATIDO


def latido(tablero: Tablero, pulsos: int = 3) -> None:
    normal = bloque_tablero(tablero)
    alerta = bloque_tablero(tablero, alerta=True)
    fotogramas = [alerta, normal] * pulsos
    efectos.repintar(fotogramas, retardo=0.26, factor=0.72)


def _secuencia_giro(
    huecos: int, destino: int, vueltas: int = VUELTAS_GIRO
) -> list[int]:
    total = vueltas * huecos + destino
    return [indice % huecos + 1 for indice in range(total)]


def animar_giro(tablero: Tablero, destino: int) -> None:
    resaltado_previo = tablero.resaltado
    fotogramas = []
    for hueco in _secuencia_giro(tablero.huecos, destino):
        tablero.resaltado = hueco
        fotogramas.append(bloque_tablero(tablero))
    tablero.resaltado = resaltado_previo
    efectos.beep("clic")
    efectos.repintar(fotogramas, retardo=0.035, factor=1.13)


def elegir_accion(marcas_restantes: int) -> str:
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
    texto = ambiente.mensaje_de_dia(dia, rng=azar)
    bitacora.registrar_accion("dia", f"Amanece el dia {dia}.")
    print()
    efectos.escribir(f"   {GRIS}{texto}{RESET}")
    efectos.pausa(1.2)


def cartel_evento(evento: str) -> None:
    efectos.beep("zumbido" if evento == "tambor_caliente" else "clic")
    efectos.banner(
        ambiente.cartel_evento(evento, eventos.texto_de(evento)),
        color=AMARILLO,
        segundos=2.0,
    )


def revelar_pista(numero: int, pista: "pistas.Pista") -> None:
    efectos.escribir(f"   {AMARILLO}#{numero}{RESET} {pista.texto}")


def _imprimir_epilogo(final: "ambiente.Epilogo", color: str) -> None:
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
    print(f"{GRIS}   Semilla de esta partida: {valor}{RESET}")
    print(f"{GRIS}   Repitela tal cual con:  --seed {valor}{RESET}")
    print()


def anunciar_rival(nombre: str, accion: str, hueco: int) -> None:
    verbos = {
        "disparar": f"apunta al hueco {hueco} y aprieta",
        "marcar": f"marca el hueco {hueco} sin disparar",
        "retirarse": "se planta y recoge lo suyo",
    }
    print()
    efectos.escribir(f"   {CELESTE}{nombre} {verbos[accion]}.{RESET}")
    efectos.pausa(1.2)


def _pedir_nombre(numero: int) -> str:
    prefijo = f"Nombre del jugador {numero} (Enter para 'Jugador {numero}'): "
    leido = input(f"{NEGRITA}   {prefijo}{RESET}").strip()
    return leido or f"Jugador {numero}"


def escena_duelo(
    activo: "jugador.Jugador",
    rival: "jugador.Jugador",
    tablero: Tablero,
) -> None:
    limpiar()
    print(NEGRITA + CELESTE + "   === EL TAMBOR DEL JUICIO: DUELO ===" + RESET)
    print(
        f"{AMARILLO}   Turno de {activo.nombre}{RESET}   ·   "
        f"{rival.nombre}: {rival.dias} dia(s) sobrevividos"
    )
    print()
    _cuerpo_de_escena(activo.disparos, activo.apuesta, activo.marca, tablero)


def resultado_duelo(jugadores: list["jugador.Jugador"]) -> None:
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
    juego: "motor.Motor"
    misrecords: "records.Records"
    resultados_farol: dict[int, str] = field(default_factory=dict)

    actor: "jugador.Jugador | None" = None


def _contar_suceso(suceso: "motor.Suceso", partida: Partida) -> None:
    juego = partida.juego
    bitacora = partida.actor.bitacora if partida.actor else juego.bitacora

    match suceso:
        case motor.EntradaInvalida():
            print(ROJO + "   Ese numero no esta en el tambor." + RESET)
        case motor.EventoTambor(tipo=tipo):
            bitacora.registrar_accion("evento", tipo.replace("_", " ").capitalize())
            cartel_evento(tipo)
        case motor.DisparoSobrevivido(en_juego=en_juego):
            efectos.beep("fallo")
            bitacora.registrar_accion(
                "disparo",
                f"Disparo al {juego.tambor.ultimo_disparo}: vacio ({en_juego} pts)",
            )
            print(
                f"{VERDE}   Click. Cartucho vacio. Lo apostado se dobla "
                f"a {en_juego} puntos.{RESET}"
            )
        case motor.PistaNueva(numero=numero, pista=pista):
            revelar_pista(numero, pista)
        case motor.DiaCompletado(dia=dia) if not juego.es_duelo():
            print(f"{AMARILLO}   Sobrevives al dia {dia}.{RESET}")
            amanecer(dia + 1, bitacora, juego.azar)
        case motor.FarolResuelto():
            _contar_farol(suceso, partida, bitacora)
        case motor.Impacto() | motor.Retirada():
            _cerrar_partida(suceso, partida)
        case motor.DueloTerminado(jugadores=jugadores):
            resultado_duelo(jugadores)


def _contar_farol(
    suceso: "motor.FarolResuelto", partida: Partida, bitacora: "historial.Historial"
) -> None:
    partida.resultados_farol[suceso.hueco] = "seguro" if suceso.acierto else "peligro"
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
        bitacora.registrar_accion("aviso", f"Farol en el {suceso.hueco}: ahi estaba")
        efectos.beep("fallo")
        print(f"{ROJO}   Farol fallido: ahi estaba la bala. Pierdes la marca.{RESET}")
    efectos.pausa(1.5)


def _cerrar_partida(final: "motor.Impacto | motor.Retirada", partida: Partida) -> None:
    bitacora = partida.actor.bitacora if partida.actor else partida.juego.bitacora
    muerto = isinstance(final, motor.Impacto)
    puntos = final.perdidos if isinstance(final, motor.Impacto) else final.ganados

    nuevo_record = final.dias > partida.misrecords.dias_maximos
    partida.misrecords.registrar_partida(
        final.dias,
        0 if muerto else puntos,
        bitacora.faroles_usados,
        bitacora.faroles_acertados,
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
    juego = partida.juego
    estados = calcular_estados(
        juego.marcadas(), partida.resultados_farol, juego.candidatos()
    )
    if oscuridad:
        estados = oscurecer(estados, juego.huecos)
    tablero = Tablero(juego.huecos, estados, juego.pistas_reveladas, juego.bitacora)

    if juego.es_duelo():
        contrario = juego.jugadores[(juego.turno + 1) % len(juego.jugadores)]
        return tablero, partial(escena_duelo, juego.jugador_activo, contrario, tablero)
    return tablero, partial(escena, juego.disparos, juego.apuesta, juego.marca, tablero)


def _nombres_del_duelo(rival_nivel: str | None) -> list[str]:
    limpiar(duro=True)
    print(NEGRITA + CELESTE + "\n   === EL TAMBOR DEL JUICIO: DUELO ===\n" + RESET)
    if rival_nivel:
        print(f"{GRIS}   Enfrente: la maquina, en modo {rival_nivel}.{RESET}\n")
        return [_pedir_nombre(1), f"La maquina ({rival_nivel})"]
    return [_pedir_nombre(1), _pedir_nombre(2)]


def _turno_de_la_maquina(
    maquina: "rival.Rival", juego: "motor.Motor"
) -> tuple[str, int]:
    yo, tu = juego.jugadores[1], juego.jugadores[0]
    accion, posicion = maquina.decidir(
        yo.dias, yo.apuesta.en_juego, tu.dias, tu.apuesta.en_juego
    )
    anunciar_rival(yo.nombre, accion, posicion)
    return accion, posicion


def _turno_del_jugador(
    juego: "motor.Motor", tablero: Tablero, dibujar: "partial[None]"
) -> tuple[str, int] | None:
    accion = elegir_accion(juego.marca.marcas_restantes)
    if accion == "retirarse":
        return accion, 0
    verbo = "Marcar" if accion == "marcar" else "Disparar a"
    elegido = elegir_hueco(tablero, dibujar, verbo)
    if elegido is None:
        return None
    refrescar(dibujar)
    return accion, elegido


def _ejecutar(
    juego: "motor.Motor",
    accion: str,
    posicion: int,
    tablero: Tablero,
    con_giro: bool,
) -> list["motor.Suceso"]:
    if accion == "retirarse":
        return juego.retirarse()
    if accion == "marcar":
        return juego.marcar(posicion)
    if con_giro:
        animar_giro(tablero, posicion)
    return juego.disparar(posicion)


def _jugar_turno(
    partida: Partida, maquina: "rival.Rival | None", oscuridad: bool
) -> None:
    juego = partida.juego
    tablero, dibujar = _pintar_turno(partida, oscuridad)
    dibujar()
    if bala_cerca(juego.marcadas(), juego.huecos):
        latido(tablero)

    eleccion: tuple[str, int] | None
    if maquina is not None and juego.turno % 2 == 1:
        eleccion = _turno_de_la_maquina(maquina, juego)
        con_giro = False
    else:
        eleccion = _turno_del_jugador(juego, tablero, dibujar)
        con_giro = True
    if eleccion is None:
        return
    accion, posicion = eleccion

    partida.actor = juego.jugador_activo
    sucesos = _ejecutar(juego, accion, posicion, tablero, con_giro)
    for suceso in sucesos:
        _contar_suceso(suceso, partida)
    if maquina is not None:
        maquina.observar(sucesos, posicion if accion == "disparar" else None)
    if accion == "disparar" and not juego.terminada:
        efectos.pausa(1.5)


def _quiere_otra(duelo: bool) -> bool:
    pregunta = "Jugar otro duelo? (s/n): " if duelo else "Jugar otra partida? (s/n): "
    otra = input(NEGRITA + f"   {pregunta}" + RESET).strip().lower()
    if otra in ("s", "si", "y", "yes"):
        return True
    print(f"{AMARILLO}   Hasta la proxima. El tambor siempre espera.{RESET}")
    return False


def jugar(
    huecos: int = estado.HUECOS,
    marcas: int = farol.MARCAS_INICIALES,
    oscuridad: bool = False,
    duelo: bool = False,
    seed: int | None = None,
    rival_nivel: str | None = None,
) -> None:
    misrecords = records.cargar()
    pendiente = seed
    nombres = _nombres_del_duelo(rival_nivel) if duelo else []

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
        maquina = (
            rival.Rival(
                rival_nivel, huecos, marcas, random.Random(semilla_partida ^ 0xB07)
            )
            if rival_nivel
            else None
        )

        limpiar(duro=True)
        if not duelo:
            amanecer(1, juego.bitacora, juego.azar)
        if pedida:
            print(f"{GRIS}   Semilla: {semilla_partida}{RESET}")

        while not juego.terminada:
            _jugar_turno(partida, maquina, oscuridad)

        sello_semilla(semilla_partida)
        if not _quiere_otra(duelo):
            break


def _version_texto() -> str:
    try:
        return version("tambor-del-juicio")
    except PackageNotFoundError:
        return "sin instalar (ejecutado directamente)"


def _parsear_args(argv: list[str] | None = None) -> argparse.Namespace:
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
        "--rival",
        choices=rival.NIVELES,
        default=None,
        help=(
            "Juega el duelo contra la maquina en vez de contra otra "
            "persona. Implica --duelo."
        ),
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
        parser.error(f"huecos debe ser al menos 2 (recibido: {args.huecos}).")
    if args.marcas < 0:
        parser.error(f"marcas no puede ser negativo (recibido: {args.marcas}).")

    if args.rival:
        args.duelo = True

    return args


def main(argv: list[str] | None = None) -> int:
    efectos.asegurar_utf8()

    args = _parsear_args(argv)

    if args.records:
        print(records.resumen(records.cargar()))
        return 0

    efectos.configurar(animaciones=not args.sin_animaciones, sonido=not args.sin_sonido)
    efectos.filtrar_color(not efectos.color_activo(sin_color=args.sin_color))

    try:
        jugar(
            huecos=args.huecos,
            marcas=args.marcas,
            oscuridad=args.oscuridad,
            duelo=args.duelo,
            seed=args.seed,
            rival_nivel=args.rival,
        )
    except (KeyboardInterrupt, EOFError) as interrupcion:
        print()
        print(AMARILLO + "   Hasta la proxima. El tambor siempre espera." + RESET)
        return 130 if isinstance(interrupcion, KeyboardInterrupt) else 0
    finally:
        efectos.cursor(True)
        efectos.filtrar_color(False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
