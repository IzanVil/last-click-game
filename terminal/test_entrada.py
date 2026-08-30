import io
import unittest
from unittest.mock import MagicMock, patch

import entrada


class TestModoTeclaDisponible(unittest.TestCase):
    def test_falso_si_la_entrada_no_es_una_terminal(self):
        with patch("entrada.sys.stdin", io.StringIO()):
            self.assertFalse(entrada.modo_tecla_disponible())

    def test_verdadero_en_unix_con_termios(self):
        with (
            patch("entrada._hay_entrada_interactiva", return_value=True),
            patch("entrada.os.name", "posix"),
            patch("entrada._modulo", return_value=object()),
        ):
            self.assertTrue(entrada.modo_tecla_disponible())

    def test_falso_en_unix_sin_termios(self):
        with (
            patch("entrada._hay_entrada_interactiva", return_value=True),
            patch("entrada.os.name", "posix"),
            patch("entrada._modulo", return_value=None),
        ):
            self.assertFalse(entrada.modo_tecla_disponible())

    def test_en_windows_mira_msvcrt(self):
        with (
            patch("entrada._hay_entrada_interactiva", return_value=True),
            patch("entrada.os.name", "nt"),
            patch("entrada._modulo", return_value=object()) as mock_modulo,
        ):
            self.assertTrue(entrada.modo_tecla_disponible())
        mock_modulo.assert_called_once_with("msvcrt")


class TestModulo(unittest.TestCase):
    def test_devuelve_el_modulo_si_existe(self):
        self.assertIs(entrada._modulo("io"), io)

    def test_devuelve_none_si_no_existe(self):
        self.assertIsNone(entrada._modulo("modulo_que_no_existe_en_ningun_sitio"))


class _TerminalFalsa:
    """Doble de sys.stdin que devuelve caracteres prefijados."""

    def __init__(self, texto):
        self._texto = iter(texto)

    def fileno(self):
        return 0

    def read(self, cuantos=1):
        return "".join(next(self._texto) for _ in range(cuantos))


def _leer_unix(texto):
    """Lee una tecla simulando una terminal Unix que entrega `texto`."""
    with (
        patch("entrada.sys.stdin", _TerminalFalsa(texto)),
        patch("entrada._modulo", return_value=MagicMock()),
    ):
        return entrada._leer_tecla_unix()


class TestLeerTeclaUnix(unittest.TestCase):
    def test_flechas(self):
        self.assertEqual(_leer_unix("\x1b[D"), entrada.IZQUIERDA)
        self.assertEqual(_leer_unix("\x1b[C"), entrada.DERECHA)
        self.assertEqual(_leer_unix("\x1b[A"), entrada.ARRIBA)
        self.assertEqual(_leer_unix("\x1b[B"), entrada.ABAJO)

    def test_secuencia_de_escape_desconocida(self):
        self.assertEqual(_leer_unix("\x1b[Z"), "")

    def test_escape_suelto(self):
        self.assertEqual(_leer_unix("\x1bX"), entrada.ESCAPE)

    def test_enter(self):
        self.assertEqual(_leer_unix("\r"), entrada.ENTER)

    def test_letra_en_minuscula(self):
        self.assertEqual(_leer_unix("Q"), "q")

    def test_ctrl_c_sale_como_interrupcion(self):
        with self.assertRaises(KeyboardInterrupt):
            _leer_unix("\x03")

    def test_restaura_los_ajustes_de_la_terminal(self):
        modulo = MagicMock()
        with (
            patch("entrada.sys.stdin", _TerminalFalsa("x")),
            patch("entrada._modulo", return_value=modulo),
        ):
            entrada._leer_tecla_unix()
        modulo.tcsetattr.assert_called_once()


class TestLeerTeclaWindows(unittest.TestCase):
    def _leer(self, caracteres):
        msvcrt = MagicMock()
        msvcrt.getwch.side_effect = list(caracteres)
        with patch("entrada._modulo", return_value=msvcrt):
            return entrada._leer_tecla_windows()

    def test_flecha_extendida(self):
        self.assertEqual(self._leer(["\xe0", "K"]), entrada.IZQUIERDA)

    def test_flecha_extendida_desconocida(self):
        self.assertEqual(self._leer(["\x00", "Z"]), "")

    def test_enter(self):
        self.assertEqual(self._leer(["\r"]), entrada.ENTER)

    def test_escape(self):
        self.assertEqual(self._leer(["\x1b"]), entrada.ESCAPE)

    def test_letra(self):
        self.assertEqual(self._leer(["D"]), "d")

    def test_ctrl_c(self):
        with self.assertRaises(KeyboardInterrupt):
            self._leer(["\x03"])


class TestLeerTecla(unittest.TestCase):
    def test_reparte_segun_el_sistema_operativo(self):
        with (
            patch("entrada.os.name", "nt"),
            patch("entrada._leer_tecla_windows", return_value="x") as mock_windows,
        ):
            self.assertEqual(entrada.leer_tecla(), "x")
        mock_windows.assert_called_once()

        with (
            patch("entrada.os.name", "posix"),
            patch("entrada._leer_tecla_unix", return_value="y") as mock_unix,
        ):
            self.assertEqual(entrada.leer_tecla(), "y")
        mock_unix.assert_called_once()


class TestSeleccionar(unittest.TestCase):
    def _seleccionar(self, teclas, huecos=8, inicio=1):
        pintados = []
        with patch("entrada.leer_tecla", side_effect=teclas):
            elegido = entrada.seleccionar(huecos, pintados.append, inicio=inicio)
        return elegido, pintados

    def test_confirma_la_seleccion_inicial(self):
        elegido, pintados = self._seleccionar([entrada.ENTER], inicio=4)
        self.assertEqual(elegido, 4)
        self.assertEqual(pintados, [4])

    def test_las_flechas_mueven_y_repintan(self):
        elegido, pintados = self._seleccionar(
            [entrada.DERECHA, entrada.DERECHA, entrada.IZQUIERDA, entrada.ENTER]
        )
        self.assertEqual(elegido, 2)
        self.assertEqual(pintados, [1, 2, 3, 2])

    def test_da_la_vuelta_por_los_dos_lados(self):
        elegido, _ = self._seleccionar([entrada.IZQUIERDA, entrada.ENTER], huecos=8)
        self.assertEqual(elegido, 8)
        elegido, _ = self._seleccionar(
            [entrada.DERECHA, entrada.ENTER], huecos=8, inicio=8
        )
        self.assertEqual(elegido, 1)

    def test_las_letras_a_y_d_tambien_mueven(self):
        elegido, _ = self._seleccionar(["d", "d", "a", entrada.ENTER], inicio=3)
        self.assertEqual(elegido, 4)

    def test_un_digito_salta_a_ese_hueco(self):
        elegido, _ = self._seleccionar(["6", entrada.ENTER])
        self.assertEqual(elegido, 6)

    def test_un_digito_fuera_del_tambor_se_ignora(self):
        elegido, pintados = self._seleccionar(["9", entrada.ENTER], huecos=6)
        self.assertEqual(elegido, 1)
        self.assertEqual(pintados, [1])

    def test_una_tecla_cualquiera_no_hace_nada(self):
        elegido, pintados = self._seleccionar(["z", entrada.ENTER], inicio=2)
        self.assertEqual(elegido, 2)
        self.assertEqual(pintados, [2])

    def test_escape_y_q_cancelan(self):
        self.assertIsNone(self._seleccionar([entrada.ESCAPE])[0])
        self.assertIsNone(self._seleccionar(["q"])[0])

    def test_el_inicio_se_recorta_al_tambor(self):
        elegido, _ = self._seleccionar([entrada.ENTER], huecos=6, inicio=99)
        self.assertEqual(elegido, 6)


if __name__ == "__main__":
    unittest.main()
