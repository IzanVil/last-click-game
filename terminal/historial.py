from dataclasses import dataclass, field
from typing import NamedTuple

MAX_ACCIONES = 5


class Accion(NamedTuple):
    tipo: str
    texto: str


@dataclass
class Historial:
    faroles_usados: int = 0
    faroles_acertados: int = 0
    eventos: dict[str, int] = field(default_factory=dict)
    acciones: list[Accion] = field(default_factory=list)

    def registrar_farol(self, acierto: bool) -> None:
        self.faroles_usados += 1
        if acierto:
            self.faroles_acertados += 1

    def registrar_evento(self, tipo: str) -> None:
        self.eventos[tipo] = self.eventos.get(tipo, 0) + 1

    def registrar_accion(self, tipo: str, texto: str) -> None:
        self.acciones.append(Accion(tipo, texto))
        del self.acciones[:-MAX_ACCIONES]

    def ultimas_acciones(self, cuantas: int = MAX_ACCIONES) -> list[Accion]:
        if cuantas <= 0:
            return []
        return self.acciones[-cuantas:]


def resumen(historial: Historial, dias: int) -> str:
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
