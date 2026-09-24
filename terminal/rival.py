"""El rival de la maquina para el modo duelo.

Hasta ahora el duelo pedia dos personas delante del mismo teclado. Esto
pone a la maquina en la silla de enfrente, apoyandose en la deduccion de
`solver.py`: el bot ve exactamente lo mismo que el jugador -- las pistas
son compartidas, los eventos se anuncian -- y saca sus propias
conclusiones. No hace trampa: no mira donde esta la bala.

Tres niveles, y ninguno se consigue haciendo fallar al bot a proposito.
Un rival que de vez en cuando tira al aire se nota y se siente tramposo;
uno que razona con menos informacion se siente humano:

- `novato`   no deduce nada, dispara donde no ha disparado todavia.
- `templado` sigue las pistas pero no deduce el patron de la bala
             (`solver.CreenciaSinPatron`).
- `implacable` deduce con todo lo que hay (`solver.Creencia`).

Ojo con `implacable`: el banco (ver banco.py) demostro que una deduccion
completa acaba acorralando la bala y entonces ya no puede morir. Contra
el, la unica forma de ganar es puntuar mas antes de que el se retire.
"""

import random
from dataclasses import dataclass

try:
    from . import motor, solver
except ImportError:  # pragma: no cover - ejecucion como script suelto
    import motor  # type: ignore[no-redef,import-not-found]
    import solver  # type: ignore[no-redef,import-not-found]

NIVELES = ("novato", "templado", "implacable")


@dataclass(frozen=True)
class Caracter:
    """Los tres numeros que distinguen a un nivel de otro."""

    # Riesgo a partir del cual prefiere gastar una marca antes que
    # disparar. En un duelo marcar CUESTA el turno (a diferencia de la
    # partida en solitario), asi que no sale gratis.
    umbral_farol: float
    # Riesgo a partir del cual se retira, pero solo si va ganando:
    # retirarse perdiendo es regalar la partida.
    umbral_retirada: float
    # Solo para el novato, que no tiene con que decidir: probabilidad de
    # plantarse en un turno cualquiera en el que vaya ganando.
    prisa_por_retirarse: float


CARACTERES = {
    # El novato no sabe lo que arriesga, asi que no farolea por miedo ni
    # calcula cuando plantarse: se planta de vez en cuando, y ya.
    "novato": Caracter(umbral_farol=2.0, umbral_retirada=2.0, prisa_por_retirarse=0.2),
    "templado": Caracter(
        umbral_farol=0.34, umbral_retirada=0.5, prisa_por_retirarse=0.0
    ),
    # El implacable aguanta mas antes de plantarse porque casi siempre
    # tiene un hueco de riesgo cero que disparar.
    "implacable": Caracter(
        umbral_farol=0.25, umbral_retirada=0.34, prisa_por_retirarse=0.0
    ),
}


class Rival:
    """Un jugador automatico que observa el duelo y decide su turno.

    Observa TODOS los turnos, no solo los suyos: el tambor y las pistas
    son compartidos, asi que lo que le pasa al humano tambien le enseña
    donde esta la bala.
    """

    def __init__(
        self,
        nivel: str,
        huecos: int,
        marcas: int,
        rng: random.Random | None = None,
    ) -> None:
        if nivel not in NIVELES:
            raise ValueError(f"Nivel de rival desconocido: {nivel}")
        self.nivel = nivel
        self.caracter = CARACTERES[nivel]
        self.huecos = huecos
        self.marcas = marcas
        self.azar = rng or random.Random()
        self.disparados: set[int] = set()
        self.creencia: solver.Creencia | None = None
        if nivel == "templado":
            self.creencia = solver.CreenciaSinPatron(huecos)
        elif nivel == "implacable":
            self.creencia = solver.Creencia(huecos)

    # --- Mirar ---------------------------------------------------------

    def observar(
        self, sucesos: list["motor.Suceso"], hueco_disparado: int | None
    ) -> None:
        """Actualiza lo que sabe con lo que acaba de pasar en la mesa.

        `hueco_disparado` es a donde se disparo, o None si el turno fue
        un farol o una retirada. Los sucesos no lo llevan dentro y hace
        falta para saber que hueco descartar.
        """
        if hueco_disparado is not None:
            self.disparados.add(hueco_disparado)

        if self.creencia is None:
            return

        sobrevivido = any(isinstance(s, motor.DisparoSobrevivido) for s in sucesos)
        if hueco_disparado is not None and sobrevivido:
            self.creencia.tras_disparo_fallido(hueco_disparado)

        miente = any(
            isinstance(s, motor.EventoTambor) and s.tipo == "tambor_caliente"
            for s in sucesos
        )
        for suceso in sucesos:
            if isinstance(suceso, motor.EventoTambor):
                if suceso.tipo == "clic_metalico":
                    self.creencia.tras_clic_metalico()
            elif isinstance(suceso, motor.PistaNueva):
                self.creencia.tras_pista(suceso.pista.candidatos, miente)
            elif isinstance(suceso, motor.FarolResuelto):
                self.creencia.tras_farol(suceso.hueco, suceso.acierto)

    # --- Decidir -------------------------------------------------------

    def _riesgo_y_hueco(self) -> tuple[float, int]:
        """El hueco mas seguro que ve y lo que cree arriesgar en el."""
        if self.creencia is None or self.creencia.contradictoria():
            sin_probar = [
                hueco
                for hueco in range(1, self.huecos + 1)
                if hueco not in self.disparados
            ]
            elegidos = sin_probar or list(range(1, self.huecos + 1))
            return 1.0 / self.huecos, self.azar.choice(elegidos)
        # Entre los empatados a riesgo minimo elige al azar: son igual
        # de seguros, y disparar siempre al mismo le daria un aire de
        # robot que no tiene por que tener.
        candidatos = self.creencia.huecos_mas_seguros()
        hueco = self.azar.choice(candidatos)
        return self.creencia.riesgo_por_hueco().get(hueco, 1.0), hueco

    def decidir(
        self, mis_dias: int, mis_puntos: int, sus_dias: int, sus_puntos: int
    ) -> tuple[str, int]:
        """Que hace en su turno: ("disparar"|"marcar"|"retirarse", hueco).

        El orden de las reglas es el orden de sus prioridades: si hay un
        hueco que sabe vacio no hay nada que pensar; si no, plantarse
        solo tiene sentido yendo por delante; y gastar una marca es el
        recurso para cuando el riesgo aprieta y aun no va ganando.
        """
        riesgo, hueco = self._riesgo_y_hueco()

        if riesgo <= 0.0:
            return "disparar", hueco

        if self._va_ganando(mis_dias, mis_puntos, sus_dias, sus_puntos):
            if riesgo >= self.caracter.umbral_retirada:
                return "retirarse", 0
            if self.azar.random() < self.caracter.prisa_por_retirarse:
                return "retirarse", 0

        if (
            self.marcas > 0
            and self.creencia is not None
            and riesgo >= self.caracter.umbral_farol
        ):
            self.marcas -= 1
            return "marcar", self.creencia.hueco_mas_probable()

        return "disparar", hueco

    @staticmethod
    def _va_ganando(
        mis_dias: int, mis_puntos: int, sus_dias: int, sus_puntos: int
    ) -> bool:
        """Con el mismo criterio con el que se decide el duelo: mandan
        los dias y, si empatan, los puntos (ver jugador.ganadores).

        Empatar cuenta como ir ganando a efectos de plantarse: si el
        duelo se cierra ahora, un empate no se pierde.
        """
        if mis_dias != sus_dias:
            return mis_dias > sus_dias
        return mis_puntos >= sus_puntos
