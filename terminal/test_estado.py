import random
import unittest

import estado


class TestMovimientoTambor(unittest.TestCase):
    def test_avanza(self):
        tambor = estado.TamborJuicio(huecos=8, patron="avanza", posicion_inicial=3)
        tambor.disparar(1)  # falla: no encuentra la bala, que se desplaza
        self.assertEqual(tambor.posicion_bala, 4)

    def test_avanza_da_la_vuelta(self):
        tambor = estado.TamborJuicio(huecos=8, patron="avanza", posicion_inicial=8)
        tambor.disparar(1)
        self.assertEqual(tambor.posicion_bala, 1)

    def test_retrocede(self):
        tambor = estado.TamborJuicio(huecos=8, patron="retrocede", posicion_inicial=3)
        tambor.disparar(1)
        self.assertEqual(tambor.posicion_bala, 2)

    def test_retrocede_da_la_vuelta(self):
        tambor = estado.TamborJuicio(huecos=8, patron="retrocede", posicion_inicial=1)
        tambor.disparar(2)
        self.assertEqual(tambor.posicion_bala, 8)

    def test_salta_dos(self):
        tambor = estado.TamborJuicio(huecos=8, patron="salta_dos", posicion_inicial=3)
        tambor.disparar(1)
        self.assertEqual(tambor.posicion_bala, 5)

    def test_salta_dos_da_la_vuelta(self):
        tambor = estado.TamborJuicio(huecos=8, patron="salta_dos", posicion_inicial=7)
        tambor.disparar(1)
        self.assertEqual(tambor.posicion_bala, 1)

    def test_espejo(self):
        tambor = estado.TamborJuicio(huecos=8, patron="espejo", posicion_inicial=3)
        tambor.disparar(1)
        self.assertEqual(tambor.posicion_bala, 6)


class TestDisparar(unittest.TestCase):
    def test_impacto_no_mueve_la_bala(self):
        tambor = estado.TamborJuicio(huecos=8, patron="avanza", posicion_inicial=3)
        self.assertTrue(tambor.disparar(3))
        self.assertEqual(tambor.posicion_bala, 3)

    def test_registra_ultimo_disparo_e_historial(self):
        tambor = estado.TamborJuicio(huecos=8, patron="avanza", posicion_inicial=3)
        tambor.disparar(1)
        tambor.disparar(2)
        self.assertEqual(tambor.ultimo_disparo, 2)
        self.assertEqual(tambor.historial, [1, 2])

    def test_rechaza_posicion_fuera_de_rango(self):
        tambor = estado.TamborJuicio(huecos=8, patron="avanza", posicion_inicial=3)
        with self.assertRaises(ValueError):
            tambor.disparar(0)
        with self.assertRaises(ValueError):
            tambor.disparar(9)


class TestConstructor(unittest.TestCase):
    def test_rechaza_huecos_insuficientes(self):
        with self.assertRaises(ValueError):
            estado.TamborJuicio(huecos=1)

    def test_rechaza_patron_desconocido(self):
        with self.assertRaises(ValueError):
            estado.TamborJuicio(patron="teletransporte")

    def test_rechaza_posicion_inicial_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            estado.TamborJuicio(huecos=8, posicion_inicial=9)

    def test_sortea_patron_y_posicion_con_rng_dado(self):
        tambor = estado.TamborJuicio(huecos=8, rng=random.Random(1))
        self.assertIn(tambor.patron, estado.PATRONES)
        self.assertTrue(1 <= tambor.posicion_bala <= 8)


if __name__ == "__main__":
    unittest.main()
