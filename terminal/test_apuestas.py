import unittest

import apuestas


class TestApuesta(unittest.TestCase):
    def test_empieza_con_la_base_en_juego(self):
        apuesta = apuestas.Apuesta(100)
        self.assertEqual(apuesta.en_juego, 100)

    def test_doblar_duplica_lo_que_hay_en_juego(self):
        apuesta = apuestas.Apuesta(100)
        self.assertEqual(apuesta.doblar(), 200)
        self.assertEqual(apuesta.doblar(), 400)

    def test_perder_lo_deja_a_cero_y_devuelve_lo_perdido(self):
        apuesta = apuestas.Apuesta(100)
        apuesta.doblar()
        perdidos = apuesta.perder()
        self.assertEqual(perdidos, 200)
        self.assertEqual(apuesta.en_juego, 0)

    def test_retirarse_devuelve_lo_en_juego_sin_tocarlo(self):
        apuesta = apuestas.Apuesta(100)
        apuesta.doblar()
        cobrado = apuesta.retirarse()
        self.assertEqual(cobrado, 200)
        self.assertEqual(apuesta.en_juego, 200)

    def test_sumar_bono_no_dobla_solo_suma(self):
        apuesta = apuestas.Apuesta(100)
        apuesta.doblar()
        self.assertEqual(apuesta.sumar_bono(50), 250)
        self.assertEqual(apuesta.en_juego, 250)

    def test_rechaza_base_no_positiva(self):
        with self.assertRaises(ValueError):
            apuestas.Apuesta(0)
        with self.assertRaises(ValueError):
            apuestas.Apuesta(-50)


if __name__ == "__main__":
    unittest.main()
