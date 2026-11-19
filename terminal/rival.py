import random
from dataclasses import dataclass

try:
    from . import motor, solver
except ImportError:  # pragma: no cover
    import motor  # type: ignore[no-redef,import-not-found]
    import solver  # type: ignore[no-redef,import-not-found]

NIVELES = ("novato", "templado", "implacable")


@dataclass(frozen=True)
class Caracter:
    umbral_farol: float
    umbral_retirada: float
    prisa_por_retirarse: float


CARACTERES = {
    "novato": Caracter(umbral_farol=2.0, umbral_retirada=2.0, prisa_por_retirarse=0.2),
    "templado": Caracter(
        umbral_farol=0.34, umbral_retirada=0.5, prisa_por_retirarse=0.0
    ),
    "implacable": Caracter(
        umbral_farol=0.25, umbral_retirada=0.34, prisa_por_retirarse=0.0
    ),
}


class Rival:
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

    def observar(
        self, sucesos: list["motor.Suceso"], hueco_disparado: int | None
    ) -> None:
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

    def _riesgo_y_hueco(self) -> tuple[float, int]:
        if self.creencia is None or self.creencia.contradictoria():
            sin_probar = [
                hueco
                for hueco in range(1, self.huecos + 1)
                if hueco not in self.disparados
            ]
            elegidos = sin_probar or list(range(1, self.huecos + 1))
            return 1.0 / self.huecos, self.azar.choice(elegidos)
        candidatos = self.creencia.huecos_mas_seguros()
        hueco = self.azar.choice(candidatos)
        return self.creencia.riesgo_por_hueco().get(hueco, 1.0), hueco

    def decidir(
        self, mis_dias: int, mis_puntos: int, sus_dias: int, sus_puntos: int
    ) -> tuple[str, int]:
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
        if mis_dias != sus_dias:
            return mis_dias > sus_dias
        return mis_puntos >= sus_puntos
