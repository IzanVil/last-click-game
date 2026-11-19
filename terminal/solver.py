from collections import Counter

try:
    from . import estado
except ImportError:  # pragma: no cover
    import estado  # type: ignore[no-redef,import-not-found]


class Creencia:
    def __init__(self, huecos: int, patrones: tuple[str, ...] | None = None) -> None:
        self.huecos = huecos
        self.estados = {
            (patron, hueco)
            for patron in (patrones or estado.PATRONES)
            for hueco in range(1, huecos + 1)
        }

    def __len__(self) -> int:
        return len(self.estados)

    def _mover_todos(self) -> None:
        self.estados = {
            (patron, estado._mover(hueco, patron, self.huecos))
            for patron, hueco in self.estados
        }

    def tras_disparo_fallido(self, hueco: int) -> None:
        self.estados = {
            (patron, posicion) for patron, posicion in self.estados if posicion != hueco
        }
        self._mover_todos()

    def tras_clic_metalico(self) -> None:
        self._mover_todos()

    def tras_pista(self, candidatos: frozenset[int], mentira: bool = False) -> None:
        if mentira:
            self.estados = {
                (patron, posicion)
                for patron, posicion in self.estados
                if posicion not in candidatos
            }
            return
        self.estados = {
            (patron, posicion)
            for patron, posicion in self.estados
            if posicion in candidatos
        }

    def tras_farol(self, hueco: int, acierto: bool) -> None:
        if acierto:
            self.estados = {
                (patron, posicion)
                for patron, posicion in self.estados
                if posicion != hueco
            }
            return
        self.estados = {
            (patron, posicion) for patron, posicion in self.estados if posicion == hueco
        }

    def posiciones_posibles(self) -> set[int]:
        return {posicion for _, posicion in self.estados}

    def patrones_posibles(self) -> set[str]:
        return {patron for patron, _ in self.estados}

    def riesgo_por_hueco(self) -> dict[int, float]:
        if not self.estados:
            return {}
        conteo = Counter(posicion for _, posicion in self.estados)
        total = len(self.estados)
        return {
            hueco: conteo.get(hueco, 0) / total for hueco in range(1, self.huecos + 1)
        }

    def hueco_mas_seguro(self) -> int:
        riesgos = self.riesgo_por_hueco()
        if not riesgos:
            return 1
        return min(riesgos, key=lambda hueco: (riesgos[hueco], hueco))

    def huecos_mas_seguros(self) -> list[int]:
        riesgos = self.riesgo_por_hueco()
        if not riesgos:
            return []
        minimo = min(riesgos.values())
        return sorted(h for h, riesgo in riesgos.items() if riesgo == minimo)

    def hueco_mas_probable(self) -> int:
        riesgos = self.riesgo_por_hueco()
        if not riesgos:
            return 1
        return max(riesgos, key=lambda hueco: (riesgos[hueco], -hueco))

    def acorralada(self) -> bool:
        return len(self.posiciones_posibles()) == 1

    def contradictoria(self) -> bool:
        return not self.estados


class CreenciaSinPatron(Creencia):
    def _mover_todos(self) -> None:
        self.estados = {
            ("?", estado._mover(posicion, patron, self.huecos))
            for _, posicion in self.estados
            for patron in estado.PATRONES
        }

    def patrones_posibles(self) -> set[str]:
        return set(estado.PATRONES)
