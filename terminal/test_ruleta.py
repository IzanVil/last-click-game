import unittest
from unittest.mock import patch

import ruleta


class FakeTambor:
    """Doble de estado.TamborJuicio con resultados de disparo prefijados."""

    def __init__(self, resultados, huecos=8):
        self.huecos = huecos
        self.posicion_bala = 5
        self.ultimo_disparo = None
        self.historial = []
        self._resultados = iter(resultados)

    def disparar(self, numero):
        self.ultimo_disparo = numero
        self.historial.append(numero)
        return next(self._resultados)


class TestElegirAccion(unittest.TestCase):
    def test_acepta_disparar(self):
        with patch("builtins.input", return_value="d"):
            self.assertEqual(ruleta.elegir_accion(), "disparar")

    def test_acepta_retirarse(self):
        with patch("builtins.input", return_value="R"):
            self.assertEqual(ruleta.elegir_accion(), "retirarse")

    def test_rechaza_entrada_invalida(self):
        entradas = iter(["x", "disparar"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            self.assertEqual(ruleta.elegir_accion(), "disparar")


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
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    def test_sobrevive_y_se_retira_con_la_apuesta_doblada(
        self, mock_tambor_cls, mock_retirada, mock_limpiar, mock_sleep
    ):
        # Un unico disparo, que no encuentra la bala (sobrevive) y luego
        # el jugador se retira: la apuesta base (100) ya se ha doblado.
        mock_tambor_cls.side_effect = lambda: FakeTambor([False])

        entradas = iter(["d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        mock_retirada.assert_called_once_with(1, 200)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.impacto")
    @patch("ruleta.estado.TamborJuicio")
    def test_impacto_pierde_todo_lo_apostado(
        self, mock_tambor_cls, mock_impacto, mock_limpiar, mock_sleep
    ):
        # Primer disparo sobrevive (100 -> 200), segundo disparo impacta:
        # se pierden los 200 puntos que estaban en juego.
        mock_tambor_cls.side_effect = lambda: FakeTambor([False, True])

        entradas = iter(["d", "3", "d", "4", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        mock_impacto.assert_called_once_with(2, 200)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_impacto_muestra_boom_y_lo_perdido(self, mock_limpiar, mock_sleep):
        with patch("builtins.print") as mock_print:
            ruleta.impacto(2, 200)

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
    def test_pantalla_retirada_muestra_lo_cobrado(self, mock_limpiar, mock_sleep):
        with patch("builtins.print") as mock_print:
            ruleta.retirada(3, 400)

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("400", mensajes)


if __name__ == "__main__":
    unittest.main()
