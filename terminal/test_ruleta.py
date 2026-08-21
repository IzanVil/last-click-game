import unittest
from unittest.mock import call, patch

import ruleta


class TestColocarBalas(unittest.TestCase):
    def test_cantidad_correcta(self):
        for cantidad in range(1, ruleta.HUECOS + 1):
            balas = ruleta.colocar_balas(cantidad)
            self.assertEqual(len(balas), cantidad)
            self.assertTrue(all(1 <= b <= ruleta.HUECOS for b in balas))

    def test_posiciones_unicas(self):
        balas = ruleta.colocar_balas(8)
        self.assertEqual(len(balas), len(set(balas)))


class TestElegirPosicion(unittest.TestCase):
    def test_valida_fuera_de_rango(self):
        entradas = iter(["0", "11", "3"])
        with patch("builtins.input", side_effect=lambda _p="": next(entradas)):
            elegida = ruleta.elegir_posicion(set())
        self.assertEqual(elegida, 3)

    def test_valida_no_numerico(self):
        entradas = iter(["abc", "5"])
        with patch("builtins.input", side_effect=lambda _p="": next(entradas)):
            elegida = ruleta.elegir_posicion(set())
        self.assertEqual(elegida, 5)

    def test_rechaza_repetida(self):
        entradas = iter(["2", "2", "4"])
        with patch("builtins.input", side_effect=lambda _p="": next(entradas)):
            elegida = ruleta.elegir_posicion({1, 2, 3})
        self.assertEqual(elegida, 4)


class TestFlujoJuego(unittest.TestCase):
    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.colocar_balas")
    def test_victoria_8_rondas(self, mock_colocar_balas, mock_limpiar, mock_sleep):
        # Bala siempre en la posicion 2..(cantidad+1); el jugador dispara
        # siempre a la posicion 1, que nunca contiene bala -> victoria.
        mock_colocar_balas.side_effect = lambda cantidad: set(range(2, cantidad + 2))

        entradas = iter(["1"] * ruleta.RONDAS + ["n"])
        with patch("builtins.input", side_effect=lambda _p="": next(entradas)), \
                patch("builtins.print"):
            ruleta.jugar()

        self.assertEqual(mock_colocar_balas.call_count, ruleta.RONDAS)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.fracaso")
    @patch("ruleta.colocar_balas")
    def test_derrota_ronda_intermedia_y_reinicio(
        self, mock_colocar_balas, mock_fracaso, mock_limpiar, mock_sleep
    ):
        # Partida 1: bala fija en la posicion 1. El jugador sobrevive a las
        # rondas 1 y 2 disparando a la posicion 2, y en la ronda 3 (una
        # ronda intermedia, no la ultima de las 8) dispara a la posicion 1
        # -> impacto. Partida 2 (tras el "reinicio"): igual que en
        # test_victoria_8_rondas, la bala esta en range(2, cantidad + 2) y
        # el jugador dispara siempre a la posicion 1 -> gana las 8 rondas,
        # lo que permite terminar jugar() de forma limpia y, de paso,
        # confirma que el bucle exterior volvio a arrancar en ronda 1 (si
        # hubiera seguido en la ronda 4 la partida 2 tendria menos de 8
        # disparos y colocar_balas no se llamaria con cantidad=1 de nuevo).
        llamadas = {"n": 0}

        def colocar_balas_por_partida(cantidad):
            llamadas["n"] += 1
            if llamadas["n"] <= 3:
                return {1}
            return set(range(2, cantidad + 2))

        mock_colocar_balas.side_effect = colocar_balas_por_partida

        entradas = iter(
            ["2", "2", "1", ""]  # partida 1: click, click, BOOM ronda 3, Enter
            + ["1"] * ruleta.RONDAS  # partida 2: gana las 8 rondas
            + ["n"]  # no quiere jugar otra vez
        )
        with patch("builtins.input", side_effect=lambda _p="": next(entradas)), \
                patch("builtins.print"):
            ruleta.jugar()

        # Se mostro la pantalla/mensaje de fracaso correspondiente a la
        # ronda intermedia en la que ocurrio el impacto (ronda 3 de 8).
        mock_fracaso.assert_called_once_with(3)

        # El bucle exterior reinicio correctamente en ronda = 1: la
        # siguiente llamada a colocar_balas tras el reinicio se hizo con
        # cantidad=1 (ronda 1), no con cantidad=4 (que seria continuar
        # donde se perdio).
        llamada_tras_reinicio = mock_colocar_balas.call_args_list[3]
        self.assertEqual(llamada_tras_reinicio, call(1))

        # 3 disparos de la partida perdida + 8 de la partida ganada.
        self.assertEqual(mock_colocar_balas.call_count, 3 + ruleta.RONDAS)

    @patch("ruleta.time.sleep", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_fracaso(self, mock_limpiar, mock_sleep):
        with patch("builtins.print") as mock_print:
            ruleta.fracaso(3)

        mensajes = " ".join(
            str(llamada.args[0]) for llamada in mock_print.call_args_list if llamada.args
        )
        # Se comprueba el contenido real (BOOM y el numero de ronda), no
        # el color exacto ni el espaciado entre letras: un cambio
        # cosmetico ahi no debe romper el test si no hay ningun bug real.
        self.assertRegex(mensajes, r"(?i)b\s*o\s*o\s*m")
        self.assertIn(str(3), mensajes)


if __name__ == "__main__":
    unittest.main()
