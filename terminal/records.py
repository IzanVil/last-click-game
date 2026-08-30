"""Récords y estadísticas de "El Tambor del Juicio", persistidos en disco.

Un JSON simple en la carpeta de datos del usuario (ver `ruta_por_defecto`),
con contadores acumulados a lo largo de todas las partidas jugadas. No
sabe nada de la interfaz: ruleta.py decide cuándo cargarlo/guardarlo y
cómo mostrarlo.
"""

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

NOMBRE_ARCHIVO = "records.json"


def ruta_por_defecto() -> Path:
    """Carpeta de datos del usuario: ~/.tambor_del_juicio/records.json.

    Path.home() ya resuelve bien en Linux/macOS/Windows sin depender de
    ninguna libreria extra; no hace falta nada mas especifico de
    plataforma para un unico fichero de texto tan pequeño como este.
    """
    return Path.home() / ".tambor_del_juicio" / NOMBRE_ARCHIVO


@dataclass
class Records:
    """Contadores acumulados a lo largo de todas las partidas jugadas."""

    partidas_jugadas: int = 0
    dias_maximos: int = 0
    puntos_maximos: int = 0
    faroles_usados: int = 0
    faroles_acertados: int = 0

    def registrar_partida(
        self, dias: int, puntos: int, faroles_usados: int, faroles_acertados: int
    ) -> None:
        """Actualiza los contadores tras una partida (gane o pierda)."""
        self.partidas_jugadas += 1
        self.dias_maximos = max(self.dias_maximos, dias)
        self.puntos_maximos = max(self.puntos_maximos, puntos)
        self.faroles_usados += faroles_usados
        self.faroles_acertados += faroles_acertados


def cargar(ruta: Path | None = None) -> Records:
    """Carga los récords desde disco.

    Si el archivo no existe todavia (primera partida) o esta corrupto,
    devuelve unos récords vacios en vez de reventar: un fichero de
    récords roto no deberia impedir jugar.
    """
    ruta = ruta or ruta_por_defecto()
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return Records()

    campos_validos = {campo.name for campo in fields(Records)}
    if not isinstance(datos, dict):
        return Records()
    datos_filtrados = {
        clave: valor for clave, valor in datos.items() if clave in campos_validos
    }
    try:
        return Records(**datos_filtrados)
    except TypeError:
        return Records()


def guardar(records: Records, ruta: Path | None = None) -> None:
    """Guarda los récords en disco, creando la carpeta si hace falta."""
    ruta = ruta or ruta_por_defecto()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(asdict(records), indent=2), encoding="utf-8")


def resumen(records: Records) -> str:
    """Frase resumen de los récords, para mostrar en pantalla."""
    if records.partidas_jugadas == 0:
        return "Todavia no hay recuerdos del tambor: esta sera tu primera partida."

    porcentaje_acierto = (
        100 * records.faroles_acertados / records.faroles_usados
        if records.faroles_usados
        else 0
    )
    return (
        f"Record: {records.dias_maximos} dia(s) sobrevividos y "
        f"{records.puntos_maximos} puntos en una sola partida, en "
        f"{records.partidas_jugadas} partida(s) jugada(s). "
        f"Faroles acertados: {records.faroles_acertados}/{records.faroles_usados} "
        f"({porcentaje_acierto:.0f}%)."
    )
