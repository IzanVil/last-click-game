"""Eventos aleatorios de "El Tambor del Juicio".

Tras sobrevivir un disparo real (no un farol), existe una probabilidad de
que ocurra un evento que anade ruido a la deduccion del jugador:

- "clic_metalico": la bala da un paso de mas, fuera de la secuencia
  normal de movimiento (ver TamborJuicio.mover_extra en estado.py).
- "tambor_caliente": la siguiente pista sera mentirosa (ver el parametro
  `mentir` de generar_pista en pistas.py).

Este modulo solo decide SI ocurre un evento y CUAL; aplicarlo (mover la
bala, marcar la siguiente pista como falsa) es cosa de quien orquesta la
partida (ruleta.py), igual que con el resto de la logica pura del juego.
"""

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
    """Sortea si ocurre un evento. Devuelve su tipo, o None si no pasa nada."""
    generador = rng or random
    if generador.random() >= probabilidad:
        return None
    return generador.choice(TIPOS_EVENTO)


def texto_de(evento: str) -> str:
    """Devuelve el texto narrativo asociado a un tipo de evento."""
    if evento not in TEXTOS:
        raise ValueError(f"Evento desconocido: {evento}")
    return TEXTOS[evento]
