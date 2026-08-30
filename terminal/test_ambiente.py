import random
import unittest

import ambiente


class TestMensajeDeDia(unittest.TestCase):
    def test_el_primer_dia_siempre_abre_igual(self):
        self.assertEqual(ambiente.mensaje_de_dia(1), ambiente.MENSAJES_DIA[0])
        self.assertEqual(ambiente.mensaje_de_dia(0), ambiente.MENSAJES_DIA[0])

    def test_los_demas_dias_sortean_otra_frase(self):
        mensaje = ambiente.mensaje_de_dia(4, rng=random.Random(1))
        self.assertIn(mensaje, ambiente.MENSAJES_DIA[1:])

    def test_el_sorteo_es_reproducible_con_la_misma_semilla(self):
        primero = ambiente.mensaje_de_dia(2, rng=random.Random(7))
        segundo = ambiente.mensaje_de_dia(2, rng=random.Random(7))
        self.assertEqual(primero, segundo)


class TestCartel(unittest.TestCase):
    def test_todas_las_lineas_miden_lo_mismo(self):
        lineas = ambiente.cartel("TITULO", "texto de abajo", ancho=20)
        self.assertEqual({len(linea) for linea in lineas}, {22})

    def test_el_titulo_va_centrado(self):
        lineas = ambiente.cartel("AB", ancho=10)
        self.assertIn("AB", lineas[2])
        self.assertTrue(lineas[2].startswith("║"))

    def test_sin_texto_el_cartel_es_mas_corto(self):
        con_texto = ambiente.cartel("T", "algo")
        sin_texto = ambiente.cartel("T")
        self.assertLess(len(sin_texto), len(con_texto))

    def test_cartel_de_evento_usa_su_titulo(self):
        lineas = ambiente.cartel_evento("clic_metalico", "se movio solo")
        contenido = "\n".join(lineas)
        self.assertIn(ambiente.TITULOS_EVENTO["clic_metalico"], contenido)
        self.assertIn("se movio solo", contenido)

    def test_cartel_de_evento_desconocido_no_revienta(self):
        lineas = ambiente.cartel_evento("terremoto", "algo pasa")
        self.assertIn("TERREMOTO", "\n".join(lineas))


class TestEpilogo(unittest.TestCase):
    def test_sin_dias_y_muerto_es_el_novato(self):
        self.assertEqual(ambiente.epilogo(0, retirado=False).titulo, "EL NOVATO")

    def test_sin_dias_pero_retirado_es_el_prudente(self):
        self.assertEqual(ambiente.epilogo(0, retirado=True).titulo, "EL PRUDENTE")

    def test_diez_dias_o_mas_son_leyenda(self):
        self.assertEqual(
            ambiente.epilogo(10, retirado=True).titulo, "LA LEYENDA DEL TAMBOR"
        )

    def test_la_leyenda_cambia_de_cierre_segun_como_acabara(self):
        retirado = ambiente.epilogo(12, retirado=True).texto
        muerto = ambiente.epilogo(12, retirado=False).texto
        self.assertNotEqual(retirado, muerto)

    def test_faroles_perfectos_dan_su_propio_final(self):
        final = ambiente.epilogo(
            2, retirado=False, faroles_usados=3, faroles_acertados=3
        )
        self.assertEqual(final.titulo, "EL LECTOR DE TAMBORES")

    def test_un_farol_fallado_ya_no_es_perfecto(self):
        final = ambiente.epilogo(
            2, retirado=False, faroles_usados=3, faroles_acertados=2
        )
        self.assertNotEqual(final.titulo, "EL LECTOR DE TAMBORES")

    def test_sobrevivir_sin_faroles_da_pulso_de_piedra(self):
        final = ambiente.epilogo(3, retirado=False, faroles_usados=0)
        self.assertEqual(final.titulo, "PULSO DE PIEDRA")

    def test_retirada_normal(self):
        final = ambiente.epilogo(
            2, retirado=True, faroles_usados=1, faroles_acertados=0, puntos=400
        )
        self.assertEqual(final.titulo, "TE RETIRAS A TIEMPO")
        self.assertIn("400", final.texto)

    def test_muerte_normal(self):
        final = ambiente.epilogo(
            2, retirado=False, faroles_usados=1, faroles_acertados=0
        )
        self.assertEqual(final.titulo, "HASTA AQUI LLEGASTE")

    def test_el_mismo_final_para_la_misma_partida(self):
        primero = ambiente.epilogo(4, retirado=True, puntos=100)
        segundo = ambiente.epilogo(4, retirado=True, puntos=100)
        self.assertEqual(primero, segundo)


if __name__ == "__main__":
    unittest.main()
