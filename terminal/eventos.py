import random

PROBABILIDAD = 0.25

TIPOS_EVENTO = ("clic_metalico", "tambor_caliente")

TEXTOS = {
    "clic_metalico": "Se oye un clic metalico. El tambor se ha movido solo.",
    "tambor_caliente": "El tambor se calienta. Desconfia de la proxima pista.",
}


def tirar_evento(
    probabilidad: float = PROBABILIDAD, rng: random.Random | None = None
) -> str | None:
    generador = rng or random
    if generador.random() >= probabilidad:
        return None
    return generador.choice(TIPOS_EVENTO)


def texto_de(evento: str) -> str:
    if evento not in TEXTOS:
        raise ValueError(f"Evento desconocido: {evento}")
    return TEXTOS[evento]
