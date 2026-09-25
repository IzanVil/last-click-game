import unittest

import apuestas
import farol
import jugador


def _jugador(nombre="", disparos=0, puntos=0):
    uno = jugador.Jugador(nombre, apuestas.Apuesta(100), farol.Farol(3))
    uno.disparos = disparos
    uno.puntos_finales = puntos
    return uno


class TestDias(unittest.TestCase):
    def test_los_dias_salen_de_los_disparos(self):
        self.assertEqual(_jugador(disparos=0).dias, 0)
        self.assertEqual(_jugador(disparos=2).dias, 0)
        self.assertEqual(_jugador(disparos=3).dias, 1)
        self.assertEqual(_jugador(disparos=7).dias, 2)


class TestMurio(unittest.TestCase):
    def test_el_tiro_fatal_no_suma_dia(self):
        caido = _jugador(disparos=3)
        self.assertEqual(caido.dias, 1)
        caido.murio = True
        self.assertEqual(caido.dias, 0)

    def test_quien_abre_ya_no_gana_solo_por_haber_disparado_mas(self):
        # Es el caso que rompia el duelo: en un duelo por turnos, el que
        # abre siempre ha disparado al menos tantas veces como el otro
        # cuando la partida se cierra. Si su tiro fatal contase como dia
        # sobrevivido, no podria perder nunca.
        caido = _jugador("Ana", disparos=3, puntos=0)
        caido.murio = True
        vivo = _jugador("Bea", disparos=2, puntos=400)
        self.assertEqual(caido.dias, vivo.dias)
        self.assertEqual(jugador.ganadores([caido, vivo]), [vivo])


class TestGanadores(unittest.TestCase):
    def test_manda_quien_sobrevivio_mas_dias(self):
        pocos = _jugador("Ana", disparos=3, puntos=9000)
        muchos = _jugador("Bea", disparos=6, puntos=1)
        self.assertEqual(jugador.ganadores([pocos, muchos]), [muchos])

    def test_con_los_mismos_dias_desempatan_los_puntos(self):
        pobre = _jugador("Ana", disparos=3, puntos=100)
        rico = _jugador("Bea", disparos=3, puntos=800)
        self.assertEqual(jugador.ganadores([pobre, rico]), [rico])

    def test_un_empate_total_no_tiene_ganador_unico(self):
        uno = _jugador("Ana", disparos=3, puntos=800)
        otro = _jugador("Bea", disparos=3, puntos=800)
        self.assertEqual(jugador.ganadores([uno, otro]), [uno, otro])

    def test_sin_jugadores_no_hay_ganadores(self):
        self.assertEqual(jugador.ganadores([]), [])


if __name__ == "__main__":
    unittest.main()
