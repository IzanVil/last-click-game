import unittest
from unittest.mock import patch

import pistas
import ruleta


class FakeTambor:
    """Doble de estado.TamborJuicio con resultados de disparo prefijados."""

    def __init__(self, resultados, huecos=8, posicion_bala=5):
        self.huecos = huecos
        self.posicion_bala = posicion_bala
        self.ultimo_disparo = None
        self.historial = []
        self._resultados = iter(resultados)
        self.movimientos_extra = 0

    def disparar(self, numero):
        self.ultimo_disparo = numero
        self.historial.append(numero)
        return next(self._resultados)

    def mover_extra(self):
        self.movimientos_extra += 1
        self.posicion_bala += 1  # desplazamiento simbolico para el test
        return self.posicion_bala


class TestCalcularEstados(unittest.TestCase):
    def test_candidato_por_defecto(self):
        estados = ruleta.calcular_estados(set(), {}, frozenset({2, 4}))
        self.assertEqual(estados, {2: "candidato", 4: "candidato"})

    def test_probado_pisa_a_candidato(self):
        estados = ruleta.calcular_estados({2}, {}, frozenset({2, 4}))
        self.assertEqual(estados[2], "probado")
        self.assertEqual(estados[4], "candidato")

    def test_resultado_de_farol_pisa_a_todo_lo_demas(self):
        estados = ruleta.calcular_estados({3}, {3: "seguro"}, frozenset({3}))
        self.assertEqual(estados[3], "seguro")


class TestDibujarTambor(unittest.TestCase):
    def test_pinta_cada_estado_con_su_glifo(self):
        estados = {1: "seguro", 2: "peligro", 3: "candidato", 4: "probado"}
        with patch("builtins.print") as mock_print:
            ruleta.dibujar_tambor(estados, huecos=4)

        filas = [str(llamada.args[0]) for llamada in mock_print.call_args_list]
        fila_celdas = filas[1]
        self.assertIn("✓", fila_celdas)
        self.assertIn("✗", fila_celdas)
        self.assertIn("?", fila_celdas)
        self.assertIn("·", fila_celdas)


class TestElegirAccion(unittest.TestCase):
    def test_acepta_disparar(self):
        with patch("builtins.input", return_value="d"):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=3), "disparar")

    def test_acepta_retirarse(self):
        with patch("builtins.input", return_value="R"):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=3), "retirarse")

    def test_acepta_marcar_si_quedan_marcas(self):
        with patch("builtins.input", return_value="m"):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=1), "marcar")

    def test_rechaza_marcar_sin_marcas_disponibles(self):
        entradas = iter(["m", "d"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=0), "disparar")

    def test_rechaza_entrada_invalida(self):
        entradas = iter(["x", "disparar"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=3), "disparar")


class TestElegirPosicion(unittest.TestCase):
    def test_valida_fuera_de_rango(self):
        entradas = iter(["0", "9", "3"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            self.assertEqual(ruleta.elegir_posicion(8), 3)

    def test_valida_no_numerico(self):
        entradas = iter(["abc", "5"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            self.assertEqual(ruleta.elegir_posicion(8), 5)


class TestFlujoJuego(unittest.TestCase):
    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    def test_sobrevive_y_se_retira_con_la_apuesta_doblada(
        self, mock_tambor_cls, mock_retirada, mock_evento, mock_limpiar, mock_sleep
    ):
        mock_tambor_cls.side_effect = lambda: FakeTambor([False])

        entradas = iter(["d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        # 1 disparo sobrevivido -> 0 dias completos (hacen falta 3) y sin
        # faroles ni eventos en el resumen.
        mock_retirada.assert_called_once_with(
            1, 200, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos."
        )

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.impacto")
    @patch("ruleta.estado.TamborJuicio")
    def test_impacto_pierde_todo_lo_apostado(
        self, mock_tambor_cls, mock_impacto, mock_evento, mock_limpiar, mock_sleep
    ):
        mock_tambor_cls.side_effect = lambda: FakeTambor([False, True])

        entradas = iter(["d", "3", "d", "4", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        mock_impacto.assert_called_once_with(
            2, 200, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos."
        )

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    def test_marcar_acertado_suma_bono_sin_disparar(
        self, mock_tambor_cls, mock_retirada, mock_evento, mock_limpiar, mock_sleep
    ):
        # posicion_bala=5 por defecto: marcar el 3 acierta (no es la bala).
        mock_tambor_cls.side_effect = lambda: FakeTambor([])

        entradas = iter(["m", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        # Marcar no cuenta como disparo (0) y suma el bono sin doblar:
        # 100 + 50 = 150. El resumen refleja el farol acertado.
        mock_retirada.assert_called_once_with(
            0, 150, 0, "Hoy sobreviviste 0 dias y faroleaste 1 vez (1 acertado)."
        )

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    def test_marcar_fallido_pierde_la_marca_sin_tocar_los_puntos(
        self, mock_tambor_cls, mock_retirada, mock_evento, mock_limpiar, mock_sleep
    ):
        # posicion_bala=5 por defecto: marcar justo el 5 falla.
        mock_tambor_cls.side_effect = lambda: FakeTambor([])

        entradas = iter(["m", "5", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        mock_retirada.assert_called_once_with(
            0, 100, 0, "Hoy sobreviviste 0 dias y faroleaste 1 vez (0 acertados)."
        )

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value="clic_metalico")
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    def test_evento_clic_metalico_mueve_la_bala_otra_vez(
        self, mock_tambor_cls, mock_retirada, mock_evento, mock_limpiar, mock_sleep
    ):
        fake = FakeTambor([False])
        mock_tambor_cls.side_effect = lambda: fake

        entradas = iter(["d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        self.assertEqual(fake.movimientos_extra, 1)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value="tambor_caliente")
    @patch("ruleta.pistas.generar_pista")
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    def test_evento_tambor_caliente_pide_una_pista_mentirosa(
        self,
        mock_tambor_cls,
        mock_retirada,
        mock_generar_pista,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        mock_tambor_cls.side_effect = lambda: FakeTambor([False])
        mock_generar_pista.return_value = pistas.Pista(
            "pista falsa", frozenset({1, 2, 3})
        )

        entradas = iter(["d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        self.assertTrue(mock_generar_pista.call_args.kwargs["mentir"])

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    def test_completa_un_dia_cada_tres_disparos_sobrevividos(
        self, mock_tambor_cls, mock_retirada, mock_evento, mock_limpiar, mock_sleep
    ):
        mock_tambor_cls.side_effect = lambda: FakeTambor([False, False, False])

        entradas = iter(["d", "1", "d", "2", "d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        # 3 disparos sobrevividos (100 -> 200 -> 400 -> 800) = 1 dia completo.
        dias, ganados, disparos = 1, 800, 3
        llamada = mock_retirada.call_args
        self.assertEqual(llamada.args[:3], (disparos, ganados, dias))
        self.assertIn("sobreviviste 1 dia", llamada.args[3])

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_impacto_muestra_boom_lo_perdido_y_el_resumen(
        self, mock_limpiar, mock_sleep
    ):
        with patch("builtins.print") as mock_print:
            ruleta.impacto(2, 200, 0, "Hoy sobreviviste 0 dias.")

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        # Se comprueba el contenido real (BOOM, los puntos perdidos y el
        # resumen), no el color exacto ni el espaciado entre letras.
        self.assertRegex(mensajes, r"(?i)b\s*o\s*o\s*m")
        self.assertIn("200", mensajes)
        self.assertIn("Hoy sobreviviste 0 dias.", mensajes)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_retirada_muestra_lo_cobrado_y_el_resumen(
        self, mock_limpiar, mock_sleep
    ):
        with patch("builtins.print") as mock_print:
            ruleta.retirada(3, 400, 1, "Hoy sobreviviste 1 dia.")

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("400", mensajes)
        self.assertIn("Hoy sobreviviste 1 dia.", mensajes)


if __name__ == "__main__":
    unittest.main()
