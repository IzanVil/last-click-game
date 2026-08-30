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


class TestAcciones(unittest.TestCase):
    def test_registrar_accion_guarda_tipo_y_texto(self):
        bitacora = historial.Historial()
        bitacora.registrar_accion("disparo", "Disparo al 3")
        self.assertEqual(
            bitacora.acciones, [historial.Accion("disparo", "Disparo al 3")]
        )

    def test_solo_se_conservan_las_ultimas(self):
        bitacora = historial.Historial()
        for numero in range(historial.MAX_ACCIONES + 3):
            bitacora.registrar_accion("disparo", f"accion {numero}")
        self.assertEqual(len(bitacora.acciones), historial.MAX_ACCIONES)
        self.assertEqual(bitacora.acciones[-1].texto, "accion 7")
        self.assertEqual(bitacora.acciones[0].texto, "accion 3")

    def test_ultimas_acciones_respeta_el_orden_de_lectura(self):
        bitacora = historial.Historial()
        for numero in range(4):
            bitacora.registrar_accion("disparo", f"accion {numero}")
        textos = [accion.texto for accion in bitacora.ultimas_acciones(2)]
        self.assertEqual(textos, ["accion 2", "accion 3"])

    def test_pedir_cero_acciones_devuelve_lista_vacia(self):
        bitacora = historial.Historial()
        bitacora.registrar_accion("dia", "Amanece el dia 1.")
        self.assertEqual(bitacora.ultimas_acciones(0), [])

    def test_las_acciones_no_se_comparten_entre_partidas(self):
        primera = historial.Historial()
        primera.registrar_accion("dia", "Amanece el dia 1.")
        self.assertEqual(historial.Historial().acciones, [])


if __name__ == "__main__":
    unittest.main()
