"""Ambientacion narrativa de "El Tambor del Juicio": voz, carteles y finales.

Texto puro: aqui no se imprime nada ni se lee del teclado, igual que en
el resto de modulos de logica. La interfaz (ruleta.py) pide una frase de
ambiente al empezar un dia, un cartel para un evento o el epilogo que
cierra la partida, y decide con que color y a que ritmo pintarlo.
"""

import random
from typing import NamedTuple

# Ancho interior de los carteles (ver `cartel`). Cabe de sobra en los 80
# caracteres de una terminal estrecha, contando el sangrado de la
# interfaz.
ANCHO_CARTEL = 46

# Frases de apertura de dia. Son solo atmosfera: ninguna dice nada del
# tambor ni de la bala, para que no se confundan con una pista.
MENSAJES_DIA: tuple[str, ...] = (
    "El reloj marca las tres de la madrugada. Nadie va a venir.",
    "Hoy el juez parece mas severo. Ni te ha mirado al entrar.",
    "Alguien ha limpiado la mesa. La mancha de ayer ya no esta.",
    "Llueve fuera. Dentro solo se oye el aceite del mecanismo.",
    "Un billete nuevo sobre el tapete. Huele a imprenta.",
    "El de la esquina lleva toda la noche sin parpadear.",
    "Han cambiado la bombilla. Ahora se te ve demasiado bien la cara.",
    "Se te ha dormido la mano izquierda. La derecha aun responde.",
    "Fuera pasa un tranvia. La mesa tiembla un segundo.",
    "Nadie ha dicho tu nombre en voz alta en toda la noche.",
)

# Cartel grande de derrota (ver ruleta.impacto).
ARTE_BOOM: tuple[str, ...] = (
    "██████   ██████   ██████  ███    ███",
    "██   ██ ██    ██ ██    ██ ████  ████",
    "██████  ██    ██ ██    ██ ██ ████ ██",
    "██   ██ ██    ██ ██    ██ ██  ██  ██",
    "██████   ██████   ██████  ██      ██",
)

# Titulo de cada evento en su cartel a pantalla completa. El texto lo
# pone eventos.texto_de: aqui solo esta como se anuncia.
TITULOS_EVENTO: dict[str, str] = {
    "clic_metalico": "C L I C   M E T A L I C O",
    "tambor_caliente": "T A M B O R   C A L I E N T E",
}


class Epilogo(NamedTuple):
    """Final alternativo: su titulo y el parrafo que lo acompania."""

    titulo: str
    texto: str


def mensaje_de_dia(dia: int, rng: random.Random | None = None) -> str:
    """Frase de ambiente para el amanecer del dia `dia`.

    El primer dia siempre abre con la misma frase (es la entrada al
    local, conviene que suene igual cada partida); a partir de ahi se
    sortea una del resto.
    """
    if dia <= 1:
        return MENSAJES_DIA[0]
    generador = rng or random
    return generador.choice(MENSAJES_DIA[1:])


def cartel(titulo: str, texto: str = "", ancho: int = ANCHO_CARTEL) -> tuple[str, ...]:
    """Monta un cartel enmarcado con el titulo (y el texto) centrados."""
    marco_superior = "╔" + "═" * ancho + "╗"
    marco_inferior = "╚" + "═" * ancho + "╝"
    vacia = "║" + " " * ancho + "║"

    lineas = [marco_superior, vacia, "║" + titulo.center(ancho) + "║"]
    if texto:
        lineas.append(vacia)
        lineas.append("║" + texto.center(ancho) + "║")
    lineas.append(vacia)
    lineas.append(marco_inferior)
    return tuple(lineas)


def cartel_evento(tipo: str, texto: str) -> tuple[str, ...]:
    """Cartel a pantalla completa para un evento del tambor."""
    return cartel(TITULOS_EVENTO.get(tipo, tipo.upper()), texto)


def epilogo(
    dias: int,
    retirado: bool,
    faroles_usados: int = 0,
    faroles_acertados: int = 0,
    puntos: int = 0,
) -> Epilogo:
    """Elige el final que merece la partida que se acaba de jugar.

    Se comprueban de lo mas especifico a lo mas general: primero las
    partidas que no llegaron a empezar, luego las gestas (muchos dias,
    faroles impecables, sangre fria sin faroles) y al final los cierres
    genericos de retirada o de muerte. Solo depende de numeros, no de la
    interfaz: la misma partida siempre cuenta el mismo final.
    """
    if dias == 0:
        if retirado:
            return Epilogo(
                "EL PRUDENTE",
                "Te levantaste antes de que el tambor aprendiera tu nombre. "
                "Nadie lo contara, y eso tambien es ganar.",
            )
        return Epilogo(
            "EL NOVATO",
            "Ni un dia. El tambor te leyo antes de que tu abrieras la boca, "
            "y la casa se quedo hasta el ultimo billete.",
        )

    if dias >= 10:
        cierre = "y te fuiste andando" if retirado else "hasta que se te acabo"
        return Epilogo(
            "LA LEYENDA DEL TAMBOR",
            f"Diez dias o mas al otro lado de la mesa, {cierre}. "
            "En este local ya no se juega: se cuenta tu historia.",
        )

    if faroles_usados >= 3 and faroles_acertados == faroles_usados:
        return Epilogo(
            "EL LECTOR DE TAMBORES",
            f"{faroles_acertados} faroles, {faroles_acertados} aciertos. "
            "No adivinabas donde estaba la bala: sabias donde no estaba.",
        )

    if faroles_usados == 0 and dias >= 3:
        return Epilogo(
            "PULSO DE PIEDRA",
            f"{dias} dias sin gastar una sola marca. Ni preguntaste. "
            "Apuntaste, disparaste y dejaste que el tambor se explicara solo.",
        )

    if retirado:
        return Epilogo(
            "TE RETIRAS A TIEMPO",
            f"{dias} dia(s) y {puntos} puntos en el bolsillo. "
            "La puerta estaba abierta y, por una vez, la usaste.",
        )

    return Epilogo(
        "HASTA AQUI LLEGASTE",
        f"{dias} dia(s) aguantando y un disparo de mas. "
        "El tambor tenia toda la noche; tu solo tenias suerte.",
    )
