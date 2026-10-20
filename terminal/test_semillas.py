import random
import unittest

import semillas


class TestNueva(unittest.TestCase):
    def test_cae_dentro_del_rango(self):
        for _ in range(100):
            valor = semillas.nueva()
            self.assertGreaterEqual(valor, 0)
            self.assertLessEqual(valor, semillas.MAXIMO)

    def test_el_generador_inyectado_la_hace_predecible(self):
        primera = semillas.nueva(random.Random(7))
        segunda = semillas.nueva(random.Random(7))
        self.assertEqual(primera, segunda)


class TestGenerador(unittest.TestCase):
    def test_la_misma_semilla_da_la_misma_secuencia(self):
        uno = semillas.generador(99)
        otro = semillas.generador(99)
        self.assertEqual(
            [uno.randint(1, 1000) for _ in range(20)],
            [otro.randint(1, 1000) for _ in range(20)],
        )

    def test_semillas_distintas_dan_secuencias_distintas(self):
        uno = [semillas.generador(1).randint(1, 1000) for _ in range(20)]
        otro = [semillas.generador(2).randint(1, 1000) for _ in range(20)]
        self.assertNotEqual(uno, otro)

    def test_da_lo_mismo_que_sembrar_el_generador_global(self):
        random.seed(1234)
        global_ = [random.randint(1, 1000) for _ in range(20)]
        propio = [semillas.generador(1234).randint(1, 1000) for _ in range(1)]
        uno = semillas.generador(1234)
        self.assertEqual([uno.randint(1, 1000) for _ in range(20)], global_)
        self.assertEqual(propio[0], global_[0])

    def test_no_toca_el_generador_global(self):
        random.seed(12345)
        esperado = [random.random() for _ in range(3)]
        random.seed(12345)
        semillas.generador(777).random()
        self.assertEqual([random.random() for _ in range(3)], esperado)


if __name__ == "__main__":
    unittest.main()
