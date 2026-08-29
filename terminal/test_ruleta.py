import unittest
from unittest.mock import patch

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

        # 1 disparo sobrevivido -> 0 dias completos (hacen falta 3).
        mock_retirada.assert_called_once_with(1, 200, 0)

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

        mock_impacto.assert_called_once_with(2, 200, 0)

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
        # 100 + 50 = 150.
        mock_retirada.assert_called_once_with(0, 150, 0)

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

        mock_retirada.assert_called_once_with(0, 100, 0)

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
    @patch("ruleta.pistas.generar_pista", return_value="pista falsa")
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
        mock_retirada.assert_called_once_with(3, 800, 1)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_impacto_muestra_boom_y_lo_perdido(self, mock_limpiar, mock_sleep):
        with patch("builtins.print") as mock_print:
            ruleta.impacto(2, 200, 0)

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        # Se comprueba el contenido real (BOOM y los puntos perdidos), no
        # el color exacto ni el espaciado entre letras.
        self.assertRegex(mensajes, r"(?i)b\s*o\s*o\s*m")
        self.assertIn("200", mensajes)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_retirada_muestra_lo_cobrado_y_los_dias(
        self, mock_limpiar, mock_sleep
    ):
        with patch("builtins.print") as mock_print:
            ruleta.retirada(3, 400, 1)

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("400", mensajes)
        self.assertIn("1 dia", mensajes)


if __name__ == "__main__":
    unittest.main()
