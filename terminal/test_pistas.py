import unittest

import pistas


class FakeRng:
    """Rng falso que registra entre que opciones se le pide elegir."""

    def __init__(self, elegido):
        self.elegido = elegido
        self.opciones_vistas = None

    def choice(self, opciones):
        self.opciones_vistas = list(opciones)
        return self.elegido


class TestPistaParidad(unittest.TestCase):
    def test_par(self):
        texto = pistas.generar_pista(4, 8, None, tipo="paridad")
        self.assertIn("par", texto)

    def test_impar(self):
        texto = pistas.generar_pista(3, 8, None, tipo="paridad")
        self.assertIn("no esta en los huecos pares", texto)


class TestPistaMitad(unittest.TestCase):
    def test_izquierda(self):
        texto = pistas.generar_pista(2, 8, None, tipo="mitad")
        self.assertIn("izquierda", texto)

    def test_derecha(self):
        texto = pistas.generar_pista(6, 8, None, tipo="mitad")
        self.assertIn("derecha", texto)

    def test_limite_pertenece_a_la_mitad_izquierda(self):
        texto = pistas.generar_pista(4, 8, None, tipo="mitad")
        self.assertIn("izquierda", texto)


class TestPistaRelativa(unittest.TestCase):
    def test_izquierda_del_ultimo_disparo(self):
        texto = pistas.generar_pista(2, 8, ultimo_disparo=5, tipo="relativa")
        self.assertIn("izquierda", texto)

    def test_derecha_del_ultimo_disparo(self):
        texto = pistas.generar_pista(7, 8, ultimo_disparo=5, tipo="relativa")
        self.assertIn("derecha", texto)

    def test_falla_sin_disparo_previo(self):
        with self.assertRaises(ValueError):
            pistas.generar_pista(2, 8, ultimo_disparo=None, tipo="relativa")


class TestPistaMentirosa(unittest.TestCase):
    def test_paridad_mentirosa_dice_lo_contrario(self):
        veraz = pistas.generar_pista(4, 8, None, tipo="paridad")
        mentira = pistas.generar_pista(4, 8, None, tipo="paridad", mentir=True)
        self.assertNotEqual(veraz, mentira)
        self.assertIn("no esta en los huecos pares", mentira)

    def test_mitad_mentirosa_dice_lo_contrario(self):
        veraz = pistas.generar_pista(2, 8, None, tipo="mitad")
        mentira = pistas.generar_pista(2, 8, None, tipo="mitad", mentir=True)
        self.assertIn("izquierda", veraz)
        self.assertIn("derecha", mentira)

    def test_relativa_mentirosa_dice_lo_contrario(self):
        veraz = pistas.generar_pista(2, 8, ultimo_disparo=5, tipo="relativa")
        mentira = pistas.generar_pista(
            2, 8, ultimo_disparo=5, tipo="relativa", mentir=True
        )
        self.assertIn("izquierda", veraz)
        self.assertIn("derecha", mentira)


class TestTipoAutomatico(unittest.TestCase):
    def test_excluye_relativa_sin_disparo_previo(self):
        rng = FakeRng("paridad")
        pistas.generar_pista(4, 8, ultimo_disparo=None, rng=rng)
        self.assertNotIn("relativa", rng.opciones_vistas)

    def test_incluye_relativa_con_disparo_previo(self):
        rng = FakeRng("paridad")
        pistas.generar_pista(4, 8, ultimo_disparo=3, rng=rng)
        self.assertIn("relativa", rng.opciones_vistas)

    def test_tipo_desconocido(self):
        with self.assertRaises(ValueError):
            pistas.generar_pista(4, 8, None, tipo="inventado")


if __name__ == "__main__":
    unittest.main()
