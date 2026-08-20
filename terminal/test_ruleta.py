import unittest
from unittest.mock import patch

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
    def test_victoria_8_rondas(self):
        original_colocar = ruleta.colocar_balas
        def balas_fijas(cantidad):
            return set(range(2, cantidad + 2))

        ruleta.colocar_balas = balas_fijas
        ruleta.limpiar = lambda: None
        ruleta.time.sleep = lambda _x: None

        entradas = iter(["1"] * ruleta.RONDAS + ["n"])
        with patch("builtins.input", side_effect=lambda _p="": next(entradas)):
            ruleta.jugar()

        ruleta.colocar_balas = original_colocar

    def test_pantalla_fracaso(self):
        ruleta.limpiar = lambda: None
        ruleta.time.sleep = lambda _x: None
        with patch("builtins.print") as mock_print:
            ruleta.fracaso(3)
        mock_print.assert_any_call('\x1b[1m\x1b[91m\n      \u2593\u2593\u2593   B O O M   \u2593\u2593\u2593\n\x1b[0m')


if __name__ == "__main__":
    unittest.main()

