import json
import unittest

import paridad


class TestTablaAlDia(unittest.TestCase):
    """La tabla versionada tiene que decir lo que Python dice hoy.

    Si alguien cambia una regla en `terminal/` y no regenera la tabla,
    este test falla antes que el de Godot: la tabla dejaria de ser la
    referencia con la que se compara la otra version. Regenerar es
    `python3 terminal/paridad.py`, y el diff resultante se revisa como
    parte del cambio.
    """

    def test_el_json_del_repo_coincide_con_la_logica_actual(self):
        guardada = json.loads(paridad.ruta_por_defecto().read_text(encoding="utf-8"))
        self.assertEqual(
            guardada,
            json.loads(json.dumps(paridad.tabla())),
            "La tabla de paridad esta desfasada: regenerala con "
            "`python3 terminal/paridad.py` y revisa el diff.",
        )

    def test_la_tabla_declara_su_formato(self):
        guardada = json.loads(paridad.ruta_por_defecto().read_text(encoding="utf-8"))
        self.assertEqual(guardada["formato"], paridad.FORMATO)


class TestCoberturaDeLaTabla(unittest.TestCase):
    """La tabla solo sirve si de verdad recorre los casos.

    Sin esto, un `continue` mal puesto podria dejarla en cuatro casos y
    seguiria pasando todo en verde en las dos versiones.
    """

    def setUp(self):
        self.tabla = paridad.tabla()

    def test_recorre_los_cuatro_patrones_en_cada_tambor(self):
        for huecos in paridad.HUECOS_PROBADOS:
            patrones = {
                c["patron"] for c in self.tabla["mover"] if c["huecos"] == huecos
            }
            self.assertEqual(patrones, set(paridad.estado.PATRONES))
            casos = [c for c in self.tabla["mover"] if c["huecos"] == huecos]
            self.assertEqual(len(casos), huecos * len(paridad.estado.PATRONES))

    def test_recorre_los_tres_tipos_de_pista_veraces_y_mentirosas(self):
        tipos = {c["tipo"] for c in self.tabla["pistas"]}
        self.assertEqual(tipos, set(paridad.pistas.TIPOS_PISTA))
        self.assertEqual({c["mentir"] for c in self.tabla["pistas"]}, {True, False})

    def test_la_relativa_nunca_sale_sin_disparo_previo(self):
        sin_disparo = [
            c
            for c in self.tabla["pistas"]
            if c["ultimo"] == -1 and c["tipo"] == "relativa"
        ]
        self.assertEqual(sin_disparo, [])

    def test_incluye_el_caso_de_la_bala_en_el_ultimo_disparo(self):
        # Es el que destapo las dos divergencias de Pistas.gd; si se
        # cayera de la tabla, la tabla dejaria de servir para lo que se
        # hizo.
        caso = next(
            c
            for c in self.tabla["pistas"]
            if c["tipo"] == "relativa"
            and c["mentir"]
            and c["posicion"] == c["ultimo"]
            and 1 < c["ultimo"] < c["huecos"]
        )
        self.assertEqual(len(caso["posibles"]), 2, "mentir puede tirar por dos lados")
        for posible in caso["posibles"]:
            self.assertNotIn("justo donde", posible["texto"])
            self.assertNotIn(caso["ultimo"], posible["candidatos"])
            self.assertTrue(posible["candidatos"])


if __name__ == "__main__":
    unittest.main()
