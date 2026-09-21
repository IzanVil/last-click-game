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
        # Es lo que permite que un test (o un futuro banco de partidas)
        # decida tambien que semillas van saliendo.
        primera = semillas.nueva(random.Random(7))
        segunda = semillas.nueva(random.Random(7))
        self.assertEqual(primera, segunda)


class TestParsear(unittest.TestCase):
    def test_acepta_un_entero_en_rango(self):
        self.assertEqual(semillas.parsear("1234"), 1234)

    def test_acepta_los_dos_extremos(self):
        self.assertEqual(semillas.parsear("0"), 0)
        self.assertEqual(semillas.parsear(str(semillas.MAXIMO)), semillas.MAXIMO)

    def test_rechaza_lo_que_no_es_un_numero(self):
        with self.assertRaises(ValueError) as capturado:
            semillas.parsear("abc")
        self.assertIn("entero", str(capturado.exception))

    def test_rechaza_un_numero_fuera_de_rango(self):
        for fuera in ("-1", str(semillas.MAXIMO + 1)):
            with self.assertRaises(ValueError) as capturado:
                semillas.parsear(fuera)
            self.assertIn("entre 0", str(capturado.exception))


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

    def test_no_toca_el_generador_global(self):
        # Si generador() sembrase random.seed(), la secuencia global
        # quedaria atada a la partida y cualquier random.* del proceso
        # le robaria numeros. Se comprueba que el global sigue donde
        # estaba tras pedir un generador de partida.
        random.seed(12345)
        esperado = [random.random() for _ in range(3)]
        random.seed(12345)
        semillas.generador(777).random()
        self.assertEqual([random.random() for _ in range(3)], esperado)


if __name__ == "__main__":
    unittest.main()
