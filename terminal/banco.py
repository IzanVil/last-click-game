"""Banco de balance: juega miles de partidas y cuenta que sale.

El balance del juego estaba fijado a ojo. Esto lo mide: enfrenta varias
politicas -- desde disparar al azar hasta deducir con `solver.Creencia`
-- contra cada preset de dificultad, y cuenta dias sobrevividos, cuanto
se tarda en acorralar la bala y cuantas partidas acaban en BOOM.

Ninguna politica se retira nunca: se juega hasta que la bala aparece o
hasta el tope de disparos. Asi el numero que sale mide la DEDUCCION y no
lo prudente que sea cada una, que es lo que se quiere comparar.

Se apoya en `motor.Motor`, no en la interfaz: por eso una partida entera
cuesta microsegundos y caben decenas de miles.

    python3 terminal/banco.py                  # 5000 partidas por caso
    python3 terminal/banco.py --partidas 50000
    python3 terminal/banco.py --duelos 500     # quien gana a quien en duelo
"""

import argparse
import random
import statistics
from dataclasses import dataclass, field

try:
    from . import estado, jugador, motor, rival, semillas, solver
except ImportError:  # pragma: no cover - ejecucion como script suelto
    import estado  # type: ignore[no-redef,import-not-found]
    import jugador  # type: ignore[no-redef,import-not-found]
    import motor  # type: ignore[no-redef,import-not-found]
    import rival  # type: ignore[no-redef,import-not-found]
    import semillas  # type: ignore[no-redef,import-not-found]
    import solver  # type: ignore[no-redef,import-not-found]

# Presets, copiados de ruleta.DIFICULTADES pero sin importar la interfaz:
# este modulo no pinta nada y no deberia arrastrar la terminal entera.
# terminal/paridad.py ya comprueba que los dos lados no se separen.
DIFICULTADES = {
    "facil": {"huecos": 10, "marcas": 4},
    "normal": {"huecos": 8, "marcas": 3},
    "dificil": {"huecos": 6, "marcas": 2},
}

# Tope de disparos por partida. Hace falta porque una politica que
# deduzca bien NO muere nunca: en cuanto sabe en que hueco esta la bala
# puede disparar a cualquier otro para siempre. Llegar al tope no es un
# empate, es una victoria; se cuenta aparte (ver `inmortales`).
TOPE_DISPAROS = 300


@dataclass
class Resultado:
    """Como acabo una partida y que se aprendio por el camino."""

    disparos: int
    dias: int
    murio: bool
    # El patron que de verdad seguia la bala. Se lee del motor al
    # terminar (el jugador no lo sabe): sirve para ver si alguno se
    # delata antes que los demas.
    patron: str
    # Disparo en el que la creencia se quedo con un unico hueco posible
    # por primera vez, o None si nunca llego a acorralarla.
    disparo_acorralada: int | None
    # Disparo en el que quedo un unico patron posible, o None.
    disparo_patron_unico: int | None
    faroles: int
    # Si la deduccion se quedo sin estados posibles. Es un fallo, no un
    # resultado: significaria que el solver y el motor no dicen lo mismo.
    contradiccion: bool


class Politica:
    """Como decide un jugador automatico. Base sin deduccion ninguna."""

    nombre = "azar"
    usa_faroles = False

    def __init__(self, huecos: int, marcas: int, rng: random.Random) -> None:
        self.huecos = huecos
        self.marcas = marcas
        self.rng = rng

    def elegir_disparo(self) -> int:
        return self.rng.randint(1, self.huecos)

    def quiere_farolear(self) -> bool:
        return False

    def elegir_farol(self) -> int:  # pragma: no cover - nunca farolea
        return 1

    # Observaciones. La politica base no aprende nada de ellas.
    def vio_disparo_fallido(self, hueco: int) -> None: ...
    def vio_clic_metalico(self) -> None: ...
    def vio_pista(self, candidatos: frozenset[int], mentira: bool) -> None: ...
    def vio_farol(self, hueco: int, acierto: bool) -> None: ...

    def acorralada(self) -> bool:
        return False

    def patron_unico(self) -> bool:
        return False

    def contradictoria(self) -> bool:
        return False


class Deductiva(Politica):
    """Lleva la cuenta exacta de lo posible y dispara a lo mas seguro."""

    nombre = "deduce"

    def __init__(self, huecos: int, marcas: int, rng: random.Random) -> None:
        super().__init__(huecos, marcas, rng)
        self.creencia = solver.Creencia(huecos)

    def elegir_disparo(self) -> int:
        return self.creencia.hueco_mas_seguro()

    def vio_disparo_fallido(self, hueco: int) -> None:
        self.creencia.tras_disparo_fallido(hueco)

    def vio_clic_metalico(self) -> None:
        self.creencia.tras_clic_metalico()

    def vio_pista(self, candidatos: frozenset[int], mentira: bool) -> None:
        self.creencia.tras_pista(candidatos, mentira)

    def vio_farol(self, hueco: int, acierto: bool) -> None:
        self.creencia.tras_farol(hueco, acierto)

    def acorralada(self) -> bool:
        return self.creencia.acorralada()

    def patron_unico(self) -> bool:
        return len(self.creencia.patrones_posibles()) == 1

    def contradictoria(self) -> bool:
        return self.creencia.contradictoria()


class DeductivaConFaroles(Deductiva):
    """Como la anterior, pero gasta marcas para acorralar antes.

    En solitario marcar no mueve la bala ni pasa turno: lo unico que
    cuesta es la marca. Asi que mientras queden marcas y la bala no este
    acorralada, farolear siempre sale a cuenta. Se marca el hueco MAS
    probable a proposito: acertando se tacha el trozo mas gordo de la
    creencia, y fallando se aprende la posicion exacta. Las dos
    respuestas valen.
    """

    nombre = "deduce+farol"
    usa_faroles = True

    def quiere_farolear(self) -> bool:
        return self.marcas > 0 and not self.creencia.acorralada()

    def elegir_farol(self) -> int:
        self.marcas -= 1
        return self.creencia.hueco_mas_probable()


POLITICAS: dict[str, type[Politica]] = {
    "azar": Politica,
    "deduce": Deductiva,
    "deduce+farol": DeductivaConFaroles,
}


def jugar_una(
    politica_cls: type[Politica],
    huecos: int,
    marcas: int,
    semilla: int,
    tope: int = TOPE_DISPAROS,
) -> Resultado:
    """Juega una partida entera contra el motor y devuelve como acabo."""
    juego = motor.Motor(huecos=huecos, marcas=marcas, rng=semillas.generador(semilla))
    # La politica sortea con un generador aparte del de la partida: si
    # compartieran, elegir un hueco al azar cambiaria el tambor y las
    # dos politicas dejarian de jugar la misma partida.
    politica = politica_cls(huecos, marcas, random.Random(semilla ^ 0x5EED))

    acorralada: int | None = None
    patron_unico: int | None = None
    faroles = 0

    while not juego.terminada and juego.disparos < tope:
        while politica.quiere_farolear():
            hueco = politica.elegir_farol()
            faroles += 1
            for suceso in juego.marcar(hueco):
                if isinstance(suceso, motor.FarolResuelto):
                    politica.vio_farol(suceso.hueco, suceso.acierto)

        disparo = politica.elegir_disparo()
        sucesos = juego.disparar(disparo)
        if any(isinstance(s, motor.Impacto) for s in sucesos):
            break

        politica.vio_disparo_fallido(disparo)
        for suceso in sucesos:
            if isinstance(suceso, motor.EventoTambor):
                if suceso.tipo == "clic_metalico":
                    politica.vio_clic_metalico()
            elif isinstance(suceso, motor.PistaNueva):
                # El aviso de tambor caliente llega ANTES que la pista,
                # asi que a estas alturas ya se sabe si miente.
                miente = any(
                    isinstance(s, motor.EventoTambor) and s.tipo == "tambor_caliente"
                    for s in sucesos
                )
                politica.vio_pista(suceso.pista.candidatos, miente)

        if acorralada is None and politica.acorralada():
            acorralada = juego.disparos
        if patron_unico is None and politica.patron_unico():
            patron_unico = juego.disparos

    return Resultado(
        disparos=juego.disparos,
        dias=estado.dias_sobrevividos(juego.disparos),
        murio=juego.terminada,
        patron=juego.tambor.patron,
        disparo_acorralada=acorralada,
        disparo_patron_unico=patron_unico,
        faroles=faroles,
        contradiccion=politica.contradictoria(),
    )


@dataclass
class Informe:
    """Lo que salio de jugar muchas partidas del mismo caso."""

    dificultad: str
    politica: str
    partidas: int
    dias: list[int] = field(default_factory=list)
    muertes: int = 0
    inmortales: int = 0
    acorraladas: list[int] = field(default_factory=list)
    patrones: list[int] = field(default_factory=list)
    contradicciones: int = 0
    # Por patron real de la bala: cuantas partidas le tocaron y, de
    # esas, en cuantos disparos se acorralo la bala. Hacen falta las
    # dos: un patron que casi nunca se acorrala saldria con una media
    # estupenda calculada sobre las cuatro veces que si se pudo.
    partidas_por_patron: dict[str, int] = field(default_factory=dict)
    por_patron: dict[str, list[int]] = field(default_factory=dict)

    @property
    def dias_medios(self) -> float:
        return statistics.mean(self.dias) if self.dias else 0.0

    @property
    def dias_mediana(self) -> float:
        return statistics.median(self.dias) if self.dias else 0.0

    @property
    def porcentaje_inmortal(self) -> float:
        return 100.0 * self.inmortales / self.partidas if self.partidas else 0.0

    @property
    def disparos_hasta_acorralar(self) -> float:
        return statistics.mean(self.acorraladas) if self.acorraladas else float("nan")

    @property
    def disparos_hasta_patron(self) -> float:
        return statistics.mean(self.patrones) if self.patrones else float("nan")


def correr(
    dificultad: str,
    politica: str,
    partidas: int,
    semilla_base: int = 0,
    tope: int = TOPE_DISPAROS,
) -> Informe:
    """Juega `partidas` del mismo caso y agrega los resultados.

    Las semillas van 0, 1, 2... a proposito: asi todas las politicas
    juegan exactamente los mismos tambores y la comparacion no depende
    de que a una le tocaran partidas mas faciles.
    """
    preset = DIFICULTADES[dificultad]
    informe = Informe(dificultad, politica, partidas)
    for indice in range(partidas):
        resultado = jugar_una(
            POLITICAS[politica],
            preset["huecos"],
            preset["marcas"],
            (semilla_base + indice) % (semillas.MAXIMO + 1),
            tope,
        )
        informe.dias.append(resultado.dias)
        informe.partidas_por_patron[resultado.patron] = (
            informe.partidas_por_patron.get(resultado.patron, 0) + 1
        )
        if resultado.murio:
            informe.muertes += 1
        else:
            informe.inmortales += 1
        if resultado.disparo_acorralada is not None:
            informe.acorraladas.append(resultado.disparo_acorralada)
            informe.por_patron.setdefault(resultado.patron, []).append(
                resultado.disparo_acorralada
            )
        if resultado.disparo_patron_unico is not None:
            informe.patrones.append(resultado.disparo_patron_unico)
        if resultado.contradiccion:
            informe.contradicciones += 1
    return informe


def _medio(valor: float) -> str:
    """Una media, o un guion cuando no hubo ni una muestra.

    Le pasa a la politica del azar, que no deduce nada y por tanto
    nunca acorrala: imprimir "nan" ahi parece un fallo de calculo
    cuando en realidad es la respuesta.
    """
    return "--" if valor != valor else f"{valor:.1f}"


def _fila(informe: Informe) -> str:
    return (
        f"{informe.dificultad:<9} {informe.politica:<13} "
        f"{informe.dias_medios:>9.1f} {informe.dias_mediana:>9.1f} "
        f"{informe.porcentaje_inmortal:>10.1f}% "
        f"{_medio(informe.disparos_hasta_acorralar):>11} "
        f"{_medio(informe.disparos_hasta_patron):>10}"
        + ("   ¡CONTRADICCIONES!" if informe.contradicciones else "")
    )


def _tabla_patrones(informe: Informe) -> list[str]:
    """Cuantos disparos cuesta acorralar la bala con cada patron.

    Es la pregunta que motivo el banco: si un patron se delata mucho
    antes que los demas, el juego tiene cuatro dificultades distintas
    sin haberlo decidido nadie.
    """
    if not informe.por_patron:
        return []
    lineas = [
        f"  por patron real de la bala ({informe.dificultad}, {informe.politica}):",
        f"    {'patron':<12} {'partidas':>9} {'acorrala':>9} {'en disparos':>12}",
    ]
    for patron in estado.PATRONES:
        jugadas = informe.partidas_por_patron.get(patron, 0)
        muestras = informe.por_patron.get(patron, [])
        if not jugadas:
            lineas.append(f"    {patron:<12} sin datos")
            continue
        porcentaje = 100.0 * len(muestras) / jugadas
        medios = f"{statistics.mean(muestras):.1f}" if muestras else "--"
        lineas.append(f"    {patron:<12} {jugadas:>9} {porcentaje:>8.1f}% {medios:>12}")
    return lineas


def informe_completo(partidas: int, tope: int = TOPE_DISPAROS) -> str:
    """La tabla entera: cada dificultad contra cada politica."""
    cabecera = (
        f"{'dificultad':<9} {'politica':<13} {'dias med':>9} {'mediana':>9} "
        f"{'sobrevive':>11} {'acorrala en':>11} {'patron en':>10}"
    )
    lineas = [
        f"{partidas} partidas por caso, tope de {tope} disparos.",
        "",
        cabecera,
        "-" * len(cabecera),
    ]
    detalle: list[str] = []
    for dificultad in ("facil", "normal", "dificil"):
        for politica in POLITICAS:
            informe = correr(dificultad, politica, partidas, tope=tope)
            lineas.append(_fila(informe))
            if politica == "deduce":
                detalle.extend(_tabla_patrones(informe))
                detalle.append("")
        lineas.append("")
    return "\n".join(lineas + detalle)


def _parsear(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="banco",
        description="Mide el balance jugando muchas partidas automaticas.",
    )
    parser.add_argument(
        "--partidas", type=int, default=5000, help="Partidas por caso (5000)."
    )
    parser.add_argument(
        "--duelos",
        type=int,
        default=0,
        help=(
            "En vez de la tabla de supervivencia, juega N duelos por "
            "cruce de niveles y cuenta quien gana a quien."
        ),
    )
    parser.add_argument(
        "--tope",
        type=int,
        default=TOPE_DISPAROS,
        help=f"Disparos maximos por partida ({TOPE_DISPAROS}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    args = _parsear(argv)
    if args.duelos:
        print(tabla_de_duelos(args.duelos))
    else:
        print(informe_completo(args.partidas, args.tope))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())


# --- Duelos: quien gana a quien -----------------------------------------------
#
# El rival de la maquina (rival.Rival) es un jugador de duelo completo:
# observa, decide y sabe cuando plantarse. Asi que para medir si un
# duelo contra la maquina es jugable basta con sentar a dos niveles
# frente a frente y contar. No hace falta una politica aparte.


def jugar_duelo(
    nivel_a: str, nivel_b: str, huecos: int, marcas: int, semilla: int, tope: int = 60
) -> str:
    """Un duelo entre dos niveles. Devuelve "a", "b" o "empate".

    Los dos ven lo mismo -- el tambor y las pistas son compartidos --,
    asi que la unica diferencia es lo que cada uno sabe sacar de ello.
    """
    juego = motor.Motor(
        huecos=huecos,
        marcas=marcas,
        nombres=["a", "b"],
        rng=semillas.generador(semilla),
    )
    bots = [
        rival.Rival(nivel_a, huecos, marcas, random.Random(semilla ^ 0xA)),
        rival.Rival(nivel_b, huecos, marcas, random.Random(semilla ^ 0xB)),
    ]

    while not juego.terminada and juego.disparos < tope:
        turno = juego.turno % 2
        yo, tu = juego.jugadores[turno], juego.jugadores[1 - turno]
        accion, hueco = bots[turno].decidir(
            yo.dias, yo.apuesta.en_juego, tu.dias, tu.apuesta.en_juego
        )
        if accion == "retirarse":
            sucesos = juego.retirarse()
        elif accion == "marcar":
            sucesos = juego.marcar(hueco)
        else:
            sucesos = juego.disparar(hueco)
        for bot in bots:
            bot.observar(sucesos, hueco if accion == "disparar" else None)

    ganadores = jugador.ganadores(juego.jugadores)
    if len(ganadores) != 1:
        return "empate"
    return "a" if ganadores[0] is juego.jugadores[0] else "b"


def tabla_de_duelos(duelos: int, dificultad: str = "normal") -> str:
    """Cada nivel contra cada nivel, para ver si alguno es imbatible.

    La pregunta que motivo el rival: si `implacable` no pierde nunca, un
    duelo contra el no es un duelo, es una demostracion.
    """
    preset = DIFICULTADES[dificultad]
    lineas = [
        f"{duelos} duelos por cruce, dificultad {dificultad}.",
        "",
        f"  {'retador':<12} {'contra':<12} {'gana':>7} {'pierde':>8} {'empata':>8}",
        "  " + "-" * 50,
    ]
    for nivel_a in rival.NIVELES:
        for nivel_b in rival.NIVELES:
            cuenta = {"a": 0, "b": 0, "empate": 0}
            for indice in range(duelos):
                cuenta[
                    jugar_duelo(
                        nivel_a, nivel_b, preset["huecos"], preset["marcas"], indice
                    )
                ] += 1
            lineas.append(
                f"  {nivel_a:<12} {nivel_b:<12} "
                f"{100.0 * cuenta['a'] / duelos:>6.1f}% "
                f"{100.0 * cuenta['b'] / duelos:>7.1f}% "
                f"{100.0 * cuenta['empate'] / duelos:>7.1f}%"
            )
        lineas.append("")
    return "\n".join(lineas)
