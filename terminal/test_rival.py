import random
import unittest

import motor
import rival
import semillas
import solver


def _rival(nivel="implacable", huecos=8, marcas=3, semilla=1):
    return rival.Rival(nivel, huecos, marcas, random.Random(semilla))


class TestNiveles(unittest.TestCase):
    def test_un_nivel_desconocido_se_rechaza(self):
        with self.assertRaises(ValueError):
            _rival("imbatible")

    def test_el_novato_no_deduce_nada(self):
        self.assertIsNone(_rival("novato").creencia)

    def test_el_templado_deduce_pero_no_sigue_el_patron(self):
        bot = _rival("templado")
        self.assertIsInstance(bot.creencia, solver.CreenciaSinPatron)
        bot.creencia.tras_disparo_fallido(1)
        self.assertEqual(bot.creencia.patrones_posibles(), set(motor.estado.PATRONES))

    def test_el_implacable_deduce_con_todo(self):
        bot = _rival("implacable")
        self.assertIsInstance(bot.creencia, solver.Creencia)
        self.assertNotIsInstance(bot.creencia, solver.CreenciaSinPatron)


class TestObservar(unittest.TestCase):
    def test_apunta_los_huecos_disparados_aunque_no_deduzca(self):
        bot = _rival("novato")
        bot.observar([], 4)
        self.assertEqual(bot.disparados, {4})

    def test_el_novato_no_repite_hueco_mientras_le_queden(self):
        bot = _rival("novato", huecos=3)
        for hueco in (1, 2):
            bot.observar([], hueco)
        _, elegido = bot._riesgo_y_hueco()
        self.assertEqual(elegido, 3)

    def test_una_pista_estrecha_la_creencia(self):
        bot = _rival("implacable")
        pista = motor.pistas.Pista("", frozenset({2, 4}))
        bot.observar([motor.PistaNueva(1, pista)], None)
        self.assertEqual(bot.creencia.posiciones_posibles(), {2, 4})

    def test_una_pista_tras_tambor_caliente_se_lee_al_reves(self):
        bot = _rival("implacable")
        pista = motor.pistas.Pista("", frozenset({2, 4, 6, 8}))
        bot.observar(
            [
                motor.EventoTambor("tambor_caliente", ""),
                motor.PistaNueva(1, pista),
            ],
            None,
        )
        self.assertEqual(bot.creencia.posiciones_posibles(), {1, 3, 5, 7})

    def test_un_farol_ajeno_tambien_enseña(self):
        # El tambor es compartido: lo que descubre el de enfrente al
        # marcar vale igual para la maquina.
        bot = _rival("implacable")
        bot.observar([motor.FarolResuelto(5, False, 100, 2, 0)], None)
        self.assertEqual(bot.creencia.posiciones_posibles(), {5})


class TestDecidir(unittest.TestCase):
    def test_dispara_sin_pensarlo_a_un_hueco_de_riesgo_cero(self):
        bot = _rival("implacable")
        bot.creencia.tras_pista(frozenset({2}))
        accion, hueco = bot.decidir(0, 100, 0, 100)
        self.assertEqual(accion, "disparar")
        self.assertNotEqual(hueco, 2)

    # Los tres siguientes usan tambores diminutos a proposito. En uno
    # de ocho huecos, estrechar la creencia a dos posiciones deja los
    # otros SEIS a riesgo cero, asi que disparar siempre es lo correcto
    # y no hay decision que probar. El riesgo solo aprieta de verdad
    # cuando la bala puede estar en cualquier hueco de los que hay.

    def test_se_planta_si_va_ganando_y_el_riesgo_aprieta(self):
        bot = _rival("implacable", huecos=2)  # 50% en cada hueco
        accion, _ = bot.decidir(mis_dias=2, mis_puntos=800, sus_dias=1, sus_puntos=100)
        self.assertEqual(accion, "retirarse")

    def test_no_se_planta_si_va_perdiendo(self):
        # Retirarse perdiendo es regalar el duelo: prefiere arriesgar.
        bot = _rival("implacable", huecos=2)
        accion, _ = bot.decidir(mis_dias=0, mis_puntos=100, sus_dias=2, sus_puntos=800)
        self.assertIn(accion, ("disparar", "marcar"))

    def test_gasta_una_marca_cuando_el_riesgo_aprieta_y_va_perdiendo(self):
        bot = _rival("implacable", huecos=3)  # 33% en cada hueco
        accion, _ = bot.decidir(0, 100, 5, 9000)
        self.assertEqual(accion, "marcar")
        self.assertEqual(bot.marcas, 2)

    def test_sin_marcas_no_puede_farolear(self):
        bot = _rival("implacable", huecos=3, marcas=0)
        accion, _ = bot.decidir(0, 100, 5, 9000)
        self.assertEqual(accion, "disparar")

    def test_una_creencia_contradictoria_no_lo_bloquea(self):
        bot = _rival("implacable")
        bot.creencia.tras_pista(frozenset())
        accion, hueco = bot.decidir(0, 100, 0, 100)
        self.assertIn(accion, ("disparar", "marcar", "retirarse"))
        self.assertIn(hueco, range(0, 9))


class TestVaGanando(unittest.TestCase):
    def test_mandan_los_dias(self):
        self.assertTrue(rival.Rival._va_ganando(2, 0, 1, 9999))
        self.assertFalse(rival.Rival._va_ganando(1, 9999, 2, 0))

    def test_empatados_a_dias_desempatan_los_puntos(self):
        self.assertTrue(rival.Rival._va_ganando(1, 800, 1, 100))
        self.assertFalse(rival.Rival._va_ganando(1, 100, 1, 800))

    def test_el_empate_total_cuenta_como_ir_ganando(self):
        # Si el duelo se cierra ahora mismo, un empate no se pierde.
        self.assertTrue(rival.Rival._va_ganando(1, 400, 1, 400))


class TestNoHaceTrampa(unittest.TestCase):
    """La verdad nunca se queda fuera de lo que el rival cree posible.

    Mismo criterio que test_solver, pero pasando por el rival entero y
    por un duelo de verdad: si alguna vez descartara el estado real,
    seria que mira donde no debe o que entiende mal alguna regla.
    """

    def test_juega_duelos_enteros_sin_descartar_la_verdad(self):
        for semilla in range(60):
            juego = motor.Motor(
                huecos=8, marcas=3, nombres=["a", "b"], rng=semillas.generador(semilla)
            )
            bot = _rival("implacable", semilla=semilla)
            for _ in range(12):
                if juego.terminada:
                    break
                accion, hueco = bot.decidir(0, 100, 0, 100)
                if accion == "retirarse":
                    sucesos = juego.retirarse()
                elif accion == "marcar":
                    sucesos = juego.marcar(hueco)
                else:
                    sucesos = juego.disparar(hueco)
                bot.observar(sucesos, hueco if accion == "disparar" else None)
                if juego.terminada:
                    break
                self.assertFalse(
                    bot.creencia.contradictoria(), f"creencia vacia (semilla {semilla})"
                )
                self.assertIn(
                    (juego.tambor.patron, juego.tambor.posicion_bala),
                    bot.creencia.estados,
                    f"el rival descarto la verdad (semilla {semilla})",
                )


if __name__ == "__main__":
    unittest.main()
