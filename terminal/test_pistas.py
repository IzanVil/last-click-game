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
        pista = pistas.generar_pista(4, 8, None, tipo="paridad")
        self.assertIn("par", pista.texto)
        self.assertEqual(pista.candidatos, frozenset({2, 4, 6, 8}))

    def test_impar(self):
        pista = pistas.generar_pista(3, 8, None, tipo="paridad")
        self.assertIn("no esta en los huecos pares", pista.texto)
        self.assertEqual(pista.candidatos, frozenset({1, 3, 5, 7}))


class TestPistaMitad(unittest.TestCase):
    def test_izquierda(self):
        pista = pistas.generar_pista(2, 8, None, tipo="mitad")
        self.assertIn("izquierda", pista.texto)
        self.assertEqual(pista.candidatos, frozenset({1, 2, 3, 4}))

    def test_derecha(self):
        pista = pistas.generar_pista(6, 8, None, tipo="mitad")
        self.assertIn("derecha", pista.texto)
        self.assertEqual(pista.candidatos, frozenset({5, 6, 7, 8}))

    def test_limite_pertenece_a_la_mitad_izquierda(self):
        pista = pistas.generar_pista(4, 8, None, tipo="mitad")
        self.assertIn("izquierda", pista.texto)


class TestPistaRelativa(unittest.TestCase):
    def test_izquierda_del_ultimo_disparo(self):
        pista = pistas.generar_pista(2, 8, ultimo_disparo=5, tipo="relativa")
        self.assertIn("izquierda", pista.texto)
        self.assertEqual(pista.candidatos, frozenset({1, 2, 3, 4}))

    def test_derecha_del_ultimo_disparo(self):
        pista = pistas.generar_pista(7, 8, ultimo_disparo=5, tipo="relativa")
        self.assertIn("derecha", pista.texto)
        self.assertEqual(pista.candidatos, frozenset({6, 7, 8}))

    def test_falla_sin_disparo_previo(self):
        with self.assertRaises(ValueError):
            pistas.generar_pista(2, 8, ultimo_disparo=None, tipo="relativa")


class TestPistaMentirosa(unittest.TestCase):
    def test_paridad_mentirosa_dice_lo_contrario(self):
        veraz = pistas.generar_pista(4, 8, None, tipo="paridad")
        mentira = pistas.generar_pista(4, 8, None, tipo="paridad", mentir=True)
        self.assertNotEqual(veraz.texto, mentira.texto)
        self.assertIn("no esta en los huecos pares", mentira.texto)
        self.assertEqual(mentira.candidatos, frozenset({1, 3, 5, 7}))

    def test_mitad_mentirosa_dice_lo_contrario(self):
        veraz = pistas.generar_pista(2, 8, None, tipo="mitad")
        mentira = pistas.generar_pista(2, 8, None, tipo="mitad", mentir=True)
        self.assertIn("izquierda", veraz.texto)
        self.assertIn("derecha", mentira.texto)
        self.assertEqual(mentira.candidatos, frozenset({5, 6, 7, 8}))

    def test_relativa_mentirosa_dice_lo_contrario(self):
        veraz = pistas.generar_pista(2, 8, ultimo_disparo=5, tipo="relativa")
        mentira = pistas.generar_pista(
            2, 8, ultimo_disparo=5, tipo="relativa", mentir=True
        )
        self.assertIn("izquierda", veraz.texto)
        self.assertIn("derecha", mentira.texto)


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


class TestInterseccion(unittest.TestCase):
    def test_vacia_sin_pistas(self):
        self.assertEqual(pistas.interseccion([]), frozenset())

    def test_una_sola_pista_es_su_propio_candidato(self):
        pista = pistas.generar_pista(4, 8, None, tipo="paridad")
        self.assertEqual(pistas.interseccion([pista]), pista.candidatos)

    def test_cruza_varias_pistas_compatibles(self):
        # Par (2,4,6,8) y mitad izquierda (1,2,3,4) -> solo 2 y 4.
        par = pistas.generar_pista(4, 8, None, tipo="paridad")
        izquierda = pistas.generar_pista(2, 8, None, tipo="mitad")
        self.assertEqual(pistas.interseccion([par, izquierda]), frozenset({2, 4}))

    def test_pistas_contradictorias_dan_interseccion_vacia(self):
        par = pistas.generar_pista(4, 8, None, tipo="paridad")
        impar = pistas.generar_pista(3, 8, None, tipo="paridad")
        self.assertEqual(pistas.interseccion([par, impar]), frozenset())


if __name__ == "__main__":
    unittest.main()
