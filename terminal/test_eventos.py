import unittest

import eventos


class FakeRng:
    """Rng falso: `random()` fijo y `choice()` devuelve el primer elemento."""

    def __init__(self, valor_random):
        self.valor_random = valor_random

    def random(self):
        return self.valor_random

    def choice(self, opciones):
        return opciones[0]


class TestTirarEvento(unittest.TestCase):
    def test_no_ocurre_evento_por_encima_de_la_probabilidad(self):
        rng = FakeRng(0.9)
        self.assertIsNone(eventos.tirar_evento(probabilidad=0.25, rng=rng))

    def test_ocurre_evento_por_debajo_de_la_probabilidad(self):
        rng = FakeRng(0.0)
        evento = eventos.tirar_evento(probabilidad=0.25, rng=rng)
        self.assertIn(evento, eventos.TIPOS_EVENTO)

    def test_limite_no_es_evento(self):
        # random() == probabilidad no debe contar como "por debajo".
        rng = FakeRng(0.25)
        self.assertIsNone(eventos.tirar_evento(probabilidad=0.25, rng=rng))


class TestTextoDe(unittest.TestCase):
    def test_devuelve_texto_para_cada_tipo_conocido(self):
        for evento in eventos.TIPOS_EVENTO:
            self.assertTrue(eventos.texto_de(evento))

    def test_tipo_desconocido(self):
        with self.assertRaises(ValueError):
            eventos.texto_de("terremoto")


if __name__ == "__main__":
    unittest.main()
