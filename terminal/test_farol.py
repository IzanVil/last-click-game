import unittest

import farol


class TestFarol(unittest.TestCase):
    def test_empieza_con_las_marcas_iniciales(self):
        marca = farol.Farol()
        self.assertEqual(marca.marcas_restantes, farol.MARCAS_INICIALES)
        self.assertTrue(marca.puede_marcar())

    def test_marcar_acierto_no_consume_menos_que_un_fallo(self):
        marca = farol.Farol(marcas=2)
        acierto = marca.marcar(hueco=3, posicion_bala=5)
        self.assertTrue(acierto)
        self.assertEqual(marca.marcas_restantes, 1)

    def test_marcar_fallo_tambien_consume_la_marca(self):
        marca = farol.Farol(marcas=2)
        acierto = marca.marcar(hueco=5, posicion_bala=5)
        self.assertFalse(acierto)
        self.assertEqual(marca.marcas_restantes, 1)

    def test_sin_marcas_no_se_puede_marcar(self):
        marca = farol.Farol(marcas=0)
        self.assertFalse(marca.puede_marcar())
        with self.assertRaises(ValueError):
            marca.marcar(hueco=1, posicion_bala=2)

    def test_rechaza_marcas_negativas(self):
        with self.assertRaises(ValueError):
            farol.Farol(marcas=-1)


if __name__ == "__main__":
    unittest.main()
