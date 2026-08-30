import io
import unittest
from unittest.mock import patch

import efectos


class _EfectosTestCase(unittest.TestCase):
    """Base que restaura los ajustes globales tras cada test."""

    def setUp(self):
        self.ajustes_previos = (
            efectos.AJUSTES.animaciones,
            efectos.AJUSTES.sonido,
        )

    def tearDown(self):
        efectos.AJUSTES.animaciones, efectos.AJUSTES.sonido = self.ajustes_previos

    def capturar(self, funcion, *args, **kwargs):
        """Ejecuta `funcion` y devuelve todo lo que escribio en pantalla."""
        salida = io.StringIO()
        with patch("efectos.sys.stdout", salida):
            funcion(*args, **kwargs)
        return salida.getvalue()


class TestConfigurar(_EfectosTestCase):
    def test_apaga_las_animaciones(self):
        efectos.configurar(animaciones=False, sonido=False)
        self.assertFalse(efectos.AJUSTES.animaciones)
        self.assertFalse(efectos.AJUSTES.sonido)

    def test_el_sonido_se_apaga_si_no_hay_terminal(self):
        with patch("efectos.hay_terminal", return_value=False):
            efectos.configurar(animaciones=True, sonido=True)
        self.assertTrue(efectos.AJUSTES.animaciones)
        self.assertFalse(efectos.AJUSTES.sonido)

    def test_el_sonido_se_enciende_si_hay_terminal(self):
        with patch("efectos.hay_terminal", return_value=True):
            efectos.configurar(animaciones=True, sonido=True)
        self.assertTrue(efectos.AJUSTES.sonido)


class TestHayTerminal(_EfectosTestCase):
    def test_falso_si_la_salida_es_un_fichero(self):
        with patch("efectos.sys.stdout", io.StringIO()):
            self.assertFalse(efectos.hay_terminal())


class TestLimpiar(_EfectosTestCase):
    def test_borra_de_forma_suave_por_defecto(self):
        efectos.AJUSTES.animaciones = True
        salida = self.capturar(efectos.limpiar)
        self.assertEqual(salida, "\033[H\033[J")

    def test_el_borrado_duro_incluye_el_historial_de_scroll(self):
        efectos.AJUSTES.animaciones = True
        salida = self.capturar(efectos.limpiar, duro=True)
        self.assertIn("\033[3J", salida)

    def test_sin_animaciones_no_toca_la_pantalla(self):
        efectos.AJUSTES.animaciones = False
        self.assertEqual(self.capturar(efectos.limpiar), "")


class TestCursor(_EfectosTestCase):
    def test_ir_a_coloca_el_cursor(self):
        efectos.AJUSTES.animaciones = True
        self.assertEqual(self.capturar(efectos.ir_a, 3, 5), "\033[3;5H")

    def test_ocultar_y_mostrar_el_cursor(self):
        efectos.AJUSTES.animaciones = True
        self.assertEqual(self.capturar(efectos.cursor, False), "\033[?25l")
        self.assertEqual(self.capturar(efectos.cursor, True), "\033[?25h")

    def test_sin_animaciones_no_se_toca_el_cursor(self):
        efectos.AJUSTES.animaciones = False
        self.assertEqual(self.capturar(efectos.cursor, True), "")


class TestPausa(_EfectosTestCase):
    def test_duerme_con_animaciones(self):
        efectos.AJUSTES.animaciones = True
        with patch("efectos.time.sleep") as mock_sleep:
            efectos.pausa(1.5)
        mock_sleep.assert_called_once_with(1.5)

    def test_no_duerme_sin_animaciones(self):
        efectos.AJUSTES.animaciones = False
        with patch("efectos.time.sleep") as mock_sleep:
            efectos.pausa(1.5)
        mock_sleep.assert_not_called()


class TestEscribir(_EfectosTestCase):
    def test_teclea_letra_a_letra_sin_esperar_en_los_codigos_de_color(self):
        efectos.AJUSTES.animaciones = True
        with patch("efectos.time.sleep") as mock_sleep:
            salida = self.capturar(
                efectos.escribir, f"{efectos.ROJO}ab c{efectos.RESET}"
            )
        self.assertEqual(salida, f"{efectos.ROJO}ab c{efectos.RESET}\n")
        # Tres letras esperan; el espacio y los dos codigos de color, no.
        self.assertEqual(mock_sleep.call_count, 3)

    def test_sin_animaciones_sale_de_una_vez_por_print(self):
        efectos.AJUSTES.animaciones = False
        with patch("builtins.print") as mock_print:
            efectos.escribir("hola")
        mock_print.assert_called_once_with("hola")

    def test_sin_salto_no_anade_linea_nueva(self):
        efectos.AJUSTES.animaciones = False
        salida = self.capturar(efectos.escribir, "hola", salto=False)
        self.assertEqual(salida, "hola")


class TestBeep(_EfectosTestCase):
    def test_suena_una_vez_por_pip_del_patron(self):
        efectos.AJUSTES.animaciones = False
        efectos.AJUSTES.sonido = True
        salida = self.capturar(efectos.beep, "impacto")
        self.assertEqual(
            salida.count(efectos.BEL), len(efectos.PATRONES_SONIDO["impacto"])
        )

    def test_callado_si_el_sonido_esta_apagado(self):
        efectos.AJUSTES.sonido = False
        self.assertEqual(self.capturar(efectos.beep, "clic"), "")

    def test_patron_desconocido(self):
        efectos.AJUSTES.sonido = True
        with self.assertRaises(ValueError):
            efectos.beep("trompeta")


class TestBloques(_EfectosTestCase):
    def test_alto_de_cuenta_las_lineas(self):
        self.assertEqual(efectos.alto_de("una"), 1)
        self.assertEqual(efectos.alto_de("una\ndos\ntres"), 3)

    def test_ancho_visible_ignora_los_codigos_de_color(self):
        self.assertEqual(
            efectos.ancho_visible(f"{efectos.NEGRITA}hola{efectos.RESET}"), 4
        )

    def test_pintar_bloque_sube_y_borra_cada_linea(self):
        efectos.AJUSTES.animaciones = True
        salida = self.capturar(efectos.pintar_bloque, "una\ndos", subir=2)
        self.assertTrue(salida.startswith("\033[2A"))
        self.assertEqual(salida.count("\033[K"), 2)

    def test_pintar_bloque_sin_animaciones_solo_imprime(self):
        efectos.AJUSTES.animaciones = False
        with patch("builtins.print") as mock_print:
            efectos.pintar_bloque("una\ndos", subir=2)
        mock_print.assert_called_once_with("una\ndos")


class TestRepintar(_EfectosTestCase):
    def test_pisa_el_bloque_anterior_en_cada_fotograma(self):
        efectos.AJUSTES.animaciones = True
        with patch("efectos.time.sleep"):
            salida = self.capturar(
                efectos.repintar, ["una\ndos", "tres\ncuatro"], retardo=0
            )
        # Dos fotogramas de dos lineas: dos subidas de dos lineas cada una
        # (la primera pisa el bloque que ya habia en pantalla).
        self.assertEqual(salida.count("\033[2A"), 2)
        self.assertIn("cuatro", salida)

    def test_la_espera_se_multiplica_por_el_factor(self):
        efectos.AJUSTES.animaciones = True
        with patch("efectos.time.sleep") as mock_sleep:
            self.capturar(efectos.repintar, ["a", "a", "a"], retardo=0.1, factor=0.5)
        esperas = [round(llamada.args[0], 4) for llamada in mock_sleep.call_args_list]
        self.assertEqual(esperas, [0.1, 0.05, 0.025])

    def test_sin_animaciones_no_pinta_nada(self):
        efectos.AJUSTES.animaciones = False
        self.assertEqual(self.capturar(efectos.repintar, ["una", "dos"]), "")

    def test_sin_fotogramas_no_pinta_nada(self):
        efectos.AJUSTES.animaciones = True
        self.assertEqual(self.capturar(efectos.repintar, []), "")


class TestBanner(_EfectosTestCase):
    def test_imprime_las_lineas_aunque_no_haya_animaciones(self):
        efectos.AJUSTES.animaciones = False
        with patch("builtins.print") as mock_print:
            efectos.banner(["ARRIBA", "ABAJO"], color=efectos.AMARILLO)
        impreso = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("ARRIBA", impreso)
        self.assertIn("ABAJO", impreso)

    def test_se_queda_en_pantalla_los_segundos_pedidos(self):
        efectos.AJUSTES.animaciones = True
        with patch("efectos.time.sleep") as mock_sleep, patch("builtins.print"):
            self.capturar(efectos.banner, ["HOLA"], segundos=2.0)
        mock_sleep.assert_called_once_with(2.0)


if __name__ == "__main__":
    unittest.main()
