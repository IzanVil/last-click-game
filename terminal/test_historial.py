import unittest

import historial


class TestHistorial(unittest.TestCase):
    def test_registrar_farol_cuenta_usos_y_aciertos(self):
        bitacora = historial.Historial()
        bitacora.registrar_farol(True)
        bitacora.registrar_farol(False)
        bitacora.registrar_farol(True)
        self.assertEqual(bitacora.faroles_usados, 3)
        self.assertEqual(bitacora.faroles_acertados, 2)

    def test_registrar_evento_cuenta_por_tipo(self):
        bitacora = historial.Historial()
        bitacora.registrar_evento("clic_metalico")
        bitacora.registrar_evento("clic_metalico")
        bitacora.registrar_evento("tambor_caliente")
        self.assertEqual(bitacora.eventos["clic_metalico"], 2)
        self.assertEqual(bitacora.eventos["tambor_caliente"], 1)


class TestResumen(unittest.TestCase):
    def test_partida_sin_faroles_ni_eventos(self):
        bitacora = historial.Historial()
        texto = historial.resumen(bitacora, dias=2)
        self.assertIn("sobreviviste 2 dias", texto)
        self.assertIn("sin faroles ni sobresaltos", texto)

    def test_partida_con_faroles_y_eventos(self):
        bitacora = historial.Historial()
        bitacora.registrar_farol(True)
        bitacora.registrar_farol(False)
        bitacora.registrar_evento("clic_metalico")
        texto = historial.resumen(bitacora, dias=5)
        self.assertIn("sobreviviste 5 dias", texto)
        self.assertIn("faroleaste 2 veces", texto)
        self.assertIn("1 acertado", texto)
        self.assertIn("1 evento", texto)

    def test_singular_de_un_dia_un_farol_y_un_evento(self):
        bitacora = historial.Historial()
        bitacora.registrar_farol(True)
        bitacora.registrar_evento("clic_metalico")
        texto = historial.resumen(bitacora, dias=1)
        self.assertIn("sobreviviste 1 dia", texto)
        self.assertNotIn("1 dias", texto)
        self.assertIn("faroleaste 1 vez", texto)
        self.assertIn("1 evento del tambor", texto)


if __name__ == "__main__":
    unittest.main()
