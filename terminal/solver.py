"""Deduccion exacta de donde esta la bala y que patron sigue.

El espacio de estados de este juego es diminuto: cuatro patrones por
ocho huecos son 32 combinaciones. Tan pequeño que no hace falta ninguna
heuristica ni ninguna aproximacion: se arranca con las 32 y se van
tachando las que contradicen lo observado. Lo que queda es exactamente
lo que un jugador perfecto podria saber en ese momento.

La posterior es uniforme sobre lo que queda, y eso no es una
simplificacion: cada observacion del juego es un filtro deterministico
(una pista descarta huecos, un disparo sobrevivido descarta uno mas) y
el tipo de pista se sortea sin mirar donde esta la bala, asi que
observar una pista concreta es igual de probable bajo cualquiera de los
estados que la cumplen. Por eso basta con contar.

Esto no es parte del juego: lo usa `banco.py` para medir el balance, y
sirve de base para un rival de verdad en el modo duelo.
"""

from collections import Counter

try:
    from . import estado
except ImportError:  # pragma: no cover - ejecucion como script suelto
    import estado  # type: ignore[no-redef,import-not-found]


class Creencia:
    """Los estados (patron, posicion) que siguen siendo posibles.

    Un "estado" es una hipotesis completa sobre el tambor: que patron
    sigue la bala y en que hueco esta ahora mismo. Se tachan segun se
    observa; nunca se añaden.
    """

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
        """Adelanta cada hipotesis segun SU patron, no segun uno comun.

        Es la unica parte que no es un filtro: cada estado se mueve por
        su cuenta, asi que dos hipotesis que hoy apuntan al mismo hueco
        pueden separarse mañana. De ahi sale casi toda la informacion
        del juego.
        """
        self.estados = {
            (patron, estado._mover(hueco, patron, self.huecos))
            for patron, hueco in self.estados
        }

    def tras_disparo_fallido(self, hueco: int) -> None:
        """Se disparo a `hueco` y la bala no estaba: se tacha y se mueve.

        El orden importa y es el del motor: primero se descarta el hueco
        (la bala no estaba ahi cuando se disparo) y solo despues se
        aplica el movimiento.
        """
        self.estados = {
            (patron, posicion) for patron, posicion in self.estados if posicion != hueco
        }
        self._mover_todos()

    def tras_clic_metalico(self) -> None:
        """El evento mueve la bala un paso mas, con su mismo patron."""
        self._mover_todos()

    def tras_pista(self, candidatos: frozenset[int], mentira: bool = False) -> None:
        """Descarta lo que la pista no deja en pie.

        Con `mentira=True` se queda con lo contrario. Una pista que se
        sabe falsa sigue siendo informacion: el juego avisa del tambor
        caliente ANTES de soltarla, asi que un jugador atento sabe
        exactamente cual miente y puede quedarse con el complemento.
        """
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
        """Marcar no mueve la bala: solo dice si estaba ahi o no.

        Fallar un farol parece malo y es justo lo contrario para la
        deduccion: deja la posicion clavada en un solo hueco.
        """
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
        """Huecos donde la bala podria estar ahora mismo."""
        return {posicion for _, posicion in self.estados}

    def patrones_posibles(self) -> set[str]:
        """Patrones que siguen encajando con todo lo visto."""
        return {patron for patron, _ in self.estados}

    def riesgo_por_hueco(self) -> dict[int, float]:
        """Probabilidad de que la bala este en cada hueco del tambor."""
        if not self.estados:
            return {}
        conteo = Counter(posicion for _, posicion in self.estados)
        total = len(self.estados)
        return {
            hueco: conteo.get(hueco, 0) / total for hueco in range(1, self.huecos + 1)
        }

    def hueco_mas_seguro(self) -> int:
        """El hueco con menos probabilidad de tener la bala.

        Ante un empate gana el numero mas bajo: da igual cual se elija
        -- el riesgo es el mismo -- pero fijarlo hace que dos partidas
        con la misma semilla se jueguen igual, que es lo que permite
        comparar dos politicas sobre el mismo tambor.
        """
        riesgos = self.riesgo_por_hueco()
        if not riesgos:
            # Creencia vacia: algo se contradijo. Que el banco lo cuente
            # en vez de reventar aqui (ver banco.Resultado.contradiccion).
            return 1
        return min(riesgos, key=lambda hueco: (riesgos[hueco], hueco))

    def huecos_mas_seguros(self) -> list[int]:
        """Todos los huecos empatados en el riesgo minimo, ordenados.

        `hueco_mas_seguro` se queda siempre con el primero para que el
        banco pueda comparar politicas sobre el mismo tambor. El rival
        de la maquina prefiere la lista entera y elegir al azar entre
        ellos: son igual de seguros, y disparar siempre al hueco 1 le
        da un aire de robot que no tiene por que tener.
        """
        riesgos = self.riesgo_por_hueco()
        if not riesgos:
            return []
        minimo = min(riesgos.values())
        return sorted(h for h, riesgo in riesgos.items() if riesgo == minimo)

    def hueco_mas_probable(self) -> int:
        """El hueco con mas papeletas: el que mejor rinde farolear.

        Acertando se tacha el hueco mas gordo, y fallando se aprende la
        posicion exacta. Las dos respuestas valen.
        """
        riesgos = self.riesgo_por_hueco()
        if not riesgos:
            return 1
        return max(riesgos, key=lambda hueco: (riesgos[hueco], -hueco))

    def acorralada(self) -> bool:
        """True si solo queda un hueco posible: el jugador ya no puede
        morir mientras siga sabiendolo (ver banco.py)."""
        return len(self.posiciones_posibles()) == 1

    def contradictoria(self) -> bool:
        """True si no queda ningun estado en pie.

        No deberia pasar nunca: significaria que el juego y esta
        deduccion no dicen lo mismo. El banco lo cuenta aparte
        precisamente para que no pase desapercibido.
        """
        return not self.estados


class CreenciaSinPatron(Creencia):
    """Sigue las pistas pero nunca deduce el patron.

    Es la diferencia entre un jugador atento y uno bueno: este apunta lo
    que dicen las pistas y descarta los huecos donde ya disparo, pero no
    lleva la cuenta de POR DONDE vino la bala, asi que cada vez que se
    mueve tiene que dar por posibles todos los destinos de cualquier
    patron. Deduce de verdad, solo que peor.

    Existe para poder graduar al rival de la maquina (ver rival.py) sin
    recurrir al truco de hacerle fallar a proposito: un rival que a
    veces tira al aire se nota y se siente tramposo, y uno que razona
    con menos informacion se siente simplemente humano.
    """

    def _mover_todos(self) -> None:
        # Se etiquetan todas igual ("?") para que dos caminos que acaban
        # en el mismo hueco cuenten como uno solo: eso es justo lo que
        # significa no saber por donde vino la bala.
        self.estados = {
            ("?", estado._mover(posicion, patron, self.huecos))
            for _, posicion in self.estados
            for patron in estado.PATRONES
        }

    def patrones_posibles(self) -> set[str]:
        """Nunca descarta un patron: no los sigue."""
        return set(estado.PATRONES)
