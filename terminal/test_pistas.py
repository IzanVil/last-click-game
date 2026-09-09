import unittest

import estado
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


class TestRelativaCuandoLaBalaCaeEnElUltimoDisparo(unittest.TestCase):
    """La bala se mueve DESPUES de un disparo fallido, asi que puede
    acabar justo en el hueco recien probado: con el patron "avanza"
    basta con disparar un hueco por delante de ella. El codigo daba por
    imposible ese caso."""

    def test_el_caso_es_alcanzable_jugando(self):
        tambor = estado.TamborJuicio(huecos=8, patron="avanza", posicion_inicial=3)
        self.assertFalse(tambor.disparar(4))  # falla: la bala estaba en 3
        self.assertEqual(tambor.posicion_bala, tambor.ultimo_disparo)

    def test_sin_mentir_dice_la_verdad(self):
        pista = pistas.generar_pista(4, 8, ultimo_disparo=4, tipo="relativa")
        self.assertIn("justo donde acabas de disparar", pista.texto)
        self.assertEqual(pista.candidatos, frozenset({4}))

    def test_mintiendo_no_regala_la_posicion_exacta(self):
        # Antes esta rama ignoraba `mentir`, asi que un evento
        # "tambor_caliente" (que existe justo para mentir) acababa
        # revelando el hueco exacto en vez de enganiar.
        pista = pistas.generar_pista(
            4, 8, ultimo_disparo=4, tipo="relativa", mentir=True
        )
        self.assertNotIn("justo donde", pista.texto)
        self.assertNotIn(4, pista.candidatos)
        self.assertTrue(pista.candidatos)  # y afirma algo, no el conjunto vacio

    def test_mintiendo_en_un_extremo_elige_el_lado_que_existe(self):
        # Disparando al hueco 1 no hay "izquierda" posible: mentir hacia
        # ese lado daria una pista con cero candidatos, que se delata
        # sola en cuanto se cruza con cualquier otra.
        for disparo, esperado in ((1, "derecha"), (8, "izquierda")):
            with self.subTest(disparo=disparo):
                pista = pistas.generar_pista(
                    disparo, 8, ultimo_disparo=disparo, tipo="relativa", mentir=True
                )
                self.assertIn(esperado, pista.texto)
                self.assertTrue(pista.candidatos)


if __name__ == "__main__":
    unittest.main()
