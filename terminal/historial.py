"""Historial de una partida de "El Tambor del Juicio" y su resumen.

No es una pantalla ni una regla del juego: solo lleva la cuenta de lo que
ha ido pasando (faroles, eventos) para poder resumirlo en una frase al
terminar la partida, gane o pierda el jugador, y guarda las ultimas
acciones para que la interfaz pueda mostrarlas en un panel.
"""

from dataclasses import dataclass, field
from typing import NamedTuple

# Cuantas acciones recientes se conservan para el panel de la interfaz.
# Mas no caben en pantalla sin robarle sitio al tambor.
MAX_ACCIONES = 5


class Accion(NamedTuple):
    """Una linea del panel de acciones recientes.

    `tipo` es una etiqueta ("disparo", "farol", "evento", "dia"...) que
    la interfaz traduce a un color; aqui no se sabe nada de colores.
    """

    tipo: str
    texto: str


@dataclass
class Historial:
    """Contadores de una partida, actualizados turno a turno."""

    faroles_usados: int = 0
    faroles_acertados: int = 0
    eventos: dict[str, int] = field(default_factory=dict)
    acciones: list[Accion] = field(default_factory=list)

    def registrar_farol(self, acierto: bool) -> None:
        """Anota un uso de farol, acertado o no."""
        self.faroles_usados += 1
        if acierto:
            self.faroles_acertados += 1

    def registrar_evento(self, tipo: str) -> None:
        """Anota que ha ocurrido un evento aleatorio de tipo `tipo`."""
        self.eventos[tipo] = self.eventos.get(tipo, 0) + 1

    def registrar_accion(self, tipo: str, texto: str) -> None:
        """Apunta una accion en el panel, tirando la mas antigua si sobra."""
        self.acciones.append(Accion(tipo, texto))
        del self.acciones[:-MAX_ACCIONES]

    def ultimas_acciones(self, cuantas: int = MAX_ACCIONES) -> list[Accion]:
        """Devuelve las ultimas `cuantas` acciones, de la mas antigua a la
        mas reciente (que es el orden en que se leen en pantalla)."""
        if cuantas <= 0:
            return []
        return self.acciones[-cuantas:]


def resumen(historial: Historial, dias: int) -> str:
    """Genera la frase narrativa final a partir de un `Historial`."""
    dia_txt = "dia" if dias == 1 else "dias"
    partes = [f"sobreviviste {dias} {dia_txt}"]

    if historial.faroles_usados:
        vez_txt = "vez" if historial.faroles_usados == 1 else "veces"
        acierto_txt = "acertado" if historial.faroles_acertados == 1 else "acertados"
        partes.append(
            f"faroleaste {historial.faroles_usados} {vez_txt} "
            f"({historial.faroles_acertados} {acierto_txt})"
        )

    total_eventos = sum(historial.eventos.values())
    if total_eventos:
        evento_txt = "evento" if total_eventos == 1 else "eventos"
        partes.append(f"viviste {total_eventos} {evento_txt} del tambor")

    if len(partes) == 1:
        return f"Hoy {partes[0]}, sin faroles ni sobresaltos."
    return "Hoy " + ", ".join(partes[:-1]) + " y " + partes[-1] + "."
