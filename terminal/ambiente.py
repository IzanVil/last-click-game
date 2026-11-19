import random
import textwrap
from typing import NamedTuple

ANCHO_CARTEL = 46

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

ARTE_BOOM: tuple[str, ...] = (
    "██████   ██████   ██████  ███    ███",
    "██   ██ ██    ██ ██    ██ ████  ████",
    "██████  ██    ██ ██    ██ ██ ████ ██",
    "██   ██ ██    ██ ██    ██ ██  ██  ██",
    "██████   ██████   ██████  ██      ██",
)

TITULOS_EVENTO: dict[str, str] = {
    "clic_metalico": "C L I C   M E T A L I C O",
    "tambor_caliente": "T A M B O R   C A L I E N T E",
}


class Epilogo(NamedTuple):
    titulo: str
    texto: str


def mensaje_de_dia(dia: int, rng: random.Random | None = None) -> str:
    if dia <= 1:
        return MENSAJES_DIA[0]
    generador = rng or random
    return generador.choice(MENSAJES_DIA[1:])


def cartel(titulo: str, texto: str = "", ancho: int = ANCHO_CARTEL) -> tuple[str, ...]:
    lineas_texto = textwrap.wrap(texto, width=ancho - 2) if texto else []
    ancho_real = max(
        [ancho, len(titulo) + 2] + [len(linea) + 2 for linea in lineas_texto]
    )

    vacia = "║" + " " * ancho_real + "║"
    lineas = [
        "╔" + "═" * ancho_real + "╗",
        vacia,
        "║" + titulo.center(ancho_real) + "║",
    ]
    if lineas_texto:
        lineas.append(vacia)
        lineas.extend("║" + linea.center(ancho_real) + "║" for linea in lineas_texto)
    lineas.append(vacia)
    lineas.append("╚" + "═" * ancho_real + "╝")
    return tuple(lineas)


def cartel_evento(tipo: str, texto: str) -> tuple[str, ...]:
    return cartel(TITULOS_EVENTO.get(tipo, tipo.upper()), texto)


def epilogo(
    dias: int,
    retirado: bool,
    faroles_usados: int = 0,
    faroles_acertados: int = 0,
    puntos: int = 0,
) -> Epilogo:
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
