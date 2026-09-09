import json
import tempfile
import unittest
from pathlib import Path

import records


class TestRegistrarPartida(unittest.TestCase):
    def test_primera_partida_fija_los_maximos(self):
        r = records.Records()
        r.registrar_partida(dias=3, puntos=400, faroles_usados=2, faroles_acertados=1)
        self.assertEqual(r.partidas_jugadas, 1)
        self.assertEqual(r.dias_maximos, 3)
        self.assertEqual(r.puntos_maximos, 400)
        self.assertEqual(r.faroles_usados, 2)
        self.assertEqual(r.faroles_acertados, 1)

    def test_una_partida_peor_no_baja_los_maximos(self):
        r = records.Records()
        r.registrar_partida(dias=5, puntos=800, faroles_usados=1, faroles_acertados=1)
        r.registrar_partida(dias=2, puntos=100, faroles_usados=1, faroles_acertados=0)
        self.assertEqual(r.partidas_jugadas, 2)
        self.assertEqual(r.dias_maximos, 5)
        self.assertEqual(r.puntos_maximos, 800)
        # Los contadores acumulativos (no maximos) si suman entre partidas.
        self.assertEqual(r.faroles_usados, 2)
        self.assertEqual(r.faroles_acertados, 1)

    def test_una_partida_mejor_si_sube_los_maximos(self):
        r = records.Records()
        r.registrar_partida(dias=2, puntos=100, faroles_usados=0, faroles_acertados=0)
        r.registrar_partida(dias=6, puntos=900, faroles_usados=0, faroles_acertados=0)
        self.assertEqual(r.dias_maximos, 6)
        self.assertEqual(r.puntos_maximos, 900)


class TestCargarGuardar(unittest.TestCase):
    def test_cargar_sin_archivo_devuelve_records_vacios(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "no-existe" / "records.json"
            r = records.cargar(ruta)
            self.assertEqual(r, records.Records())

    def test_guardar_y_recargar_conserva_los_datos(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "records.json"
            original = records.Records(
                partidas_jugadas=4,
                dias_maximos=7,
                puntos_maximos=1600,
                faroles_usados=5,
                faroles_acertados=3,
            )
            records.guardar(original, ruta)
            recargado = records.cargar(ruta)
            self.assertEqual(recargado, original)

    def test_cargar_archivo_corrupto_no_revienta(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "records.json"
            ruta.write_text("esto no es json valido {{{", encoding="utf-8")
            r = records.cargar(ruta)
            self.assertEqual(r, records.Records())

    def test_cargar_ignora_claves_desconocidas(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "records.json"
            ruta.write_text(
                json.dumps({"dias_maximos": 3, "campo_futuro_desconocido": "x"}),
                encoding="utf-8",
            )
            r = records.cargar(ruta)
            self.assertEqual(r.dias_maximos, 3)

    def test_cargar_contenido_no_es_un_objeto(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "records.json"
            ruta.write_text("[1, 2, 3]", encoding="utf-8")
            r = records.cargar(ruta)
            self.assertEqual(r, records.Records())

    def test_guardar_crea_las_carpetas_que_falten(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "a" / "b" / "records.json"
            records.guardar(records.Records(dias_maximos=1), ruta)
            self.assertTrue(ruta.exists())


class TestResumen(unittest.TestCase):
    def test_sin_partidas_jugadas(self):
        texto = records.resumen(records.Records())
        self.assertIn("Todavia no hay recuerdos", texto)

    def test_con_partidas_incluye_los_datos_clave(self):
        r = records.Records(
            partidas_jugadas=3,
            dias_maximos=5,
            puntos_maximos=800,
            faroles_usados=4,
            faroles_acertados=2,
        )
        texto = records.resumen(r)
        self.assertIn("5 dia(s)", texto)
        self.assertIn("800 puntos", texto)
        self.assertIn("3 partida(s)", texto)
        self.assertIn("2/4", texto)
        self.assertIn("50%", texto)

    def test_sin_faroles_no_divide_por_cero(self):
        r = records.Records(partidas_jugadas=1, dias_maximos=1, puntos_maximos=100)
        texto = records.resumen(r)
        self.assertIn("0/0", texto)


class TestCargarCorrupto(unittest.TestCase):
    """cargar() promete no reventar con un fichero roto: un records
    corrupto no deberia impedir jugar. Estos son los dos casos en los
    que esa promesa no se cumplia."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.ruta = Path(self.dir.name) / "records.json"

    def test_fichero_que_no_es_utf8_no_revienta(self):
        # Antes se capturaba json.JSONDecodeError a mano, pero unos bytes
        # que no son UTF-8 fallan antes, en read_text(), con
        # UnicodeDecodeError: el juego no arrancaba.
        self.ruta.write_bytes(b"\xff\xfe{}")
        self.assertEqual(records.cargar(self.ruta), records.Records())

    def test_valores_de_tipo_erroneo_caen_al_valor_por_defecto(self):
        # El JSON es valido, asi que cargaba tal cual: los contadores
        # quedaban con un str/None dentro y la partida estallaba mucho
        # despues, al registrar el resultado (`+= 1` sobre un str).
        self.ruta.write_text(
            json.dumps(
                {
                    "partidas_jugadas": "muchas",
                    "dias_maximos": None,
                    "puntos_maximos": True,
                    "faroles_usados": -3,
                    "faroles_acertados": 7,
                }
            ),
            encoding="utf-8",
        )
        cargados = records.cargar(self.ruta)

        # Solo sobrevive el unico contador que era un entero valido.
        self.assertEqual(cargados, records.Records(faroles_acertados=7))
        # Y lo cargado se puede usar sin que reviente al cerrar partida.
        cargados.registrar_partida(
            dias=2, puntos=10, faroles_usados=1, faroles_acertados=1
        )
        self.assertEqual(cargados.partidas_jugadas, 1)

    def test_ida_y_vuelta_de_un_fichero_sano(self):
        # La red de seguridad no debe cargarse el caso normal.
        original = records.Records(
            partidas_jugadas=2, dias_maximos=4, puntos_maximos=64
        )
        records.guardar(original, self.ruta)
        self.assertEqual(records.cargar(self.ruta), original)


if __name__ == "__main__":
    unittest.main()
