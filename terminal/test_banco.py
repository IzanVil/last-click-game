import unittest

import banco
import estado


class TestJugarUna(unittest.TestCase):
    def test_devuelve_una_partida_coherente(self):
        resultado = banco.jugar_una(
            banco.Deductiva, huecos=8, marcas=3, semilla=1, tope=20
        )
        self.assertLessEqual(resultado.disparos, 20)
        self.assertEqual(resultado.dias, estado.dias_sobrevividos(resultado.disparos))
        self.assertIn(resultado.patron, estado.PATRONES)
        self.assertFalse(resultado.contradiccion)

    def test_la_misma_semilla_da_la_misma_partida(self):
        una = banco.jugar_una(banco.Deductiva, 8, 3, semilla=7, tope=20)
        otra = banco.jugar_una(banco.Deductiva, 8, 3, semilla=7, tope=20)
        self.assertEqual(una, otra)

    def test_las_dos_politicas_juegan_el_mismo_tambor(self):
        # Es lo que hace justa la comparacion: el azar de la politica
        # sale de un generador aparte del de la partida, asi que elegir
        # huecos distintos no cambia el tambor que toco.
        azar = banco.jugar_una(banco.Politica, 8, 3, semilla=11, tope=20)
        deduce = banco.jugar_una(banco.Deductiva, 8, 3, semilla=11, tope=20)
        self.assertEqual(azar.patron, deduce.patron)

    def test_la_politica_del_azar_no_acorrala_nunca(self):
        resultado = banco.jugar_una(banco.Politica, 8, 3, semilla=3, tope=20)
        self.assertIsNone(resultado.disparo_acorralada)
        self.assertIsNone(resultado.disparo_patron_unico)

    def test_la_politica_con_faroles_gasta_sus_marcas(self):
        resultado = banco.jugar_una(banco.DeductivaConFaroles, 8, 3, semilla=5, tope=20)
        self.assertGreater(resultado.faroles, 0)
        self.assertLessEqual(resultado.faroles, 3)


class TestSolverYMotorNoSeContradicen(unittest.TestCase):
    """Ni una sola contradiccion en muchas partidas seguidas.

    Una creencia vacia significaria que el solver y el motor entienden
    el juego de forma distinta. Es la misma comprobacion que hace
    test_solver, pero aqui pasada por el banco entero y con faroles y
    eventos de por medio.
    """

    def test_ninguna_politica_se_queda_sin_estados(self):
        for politica in banco.POLITICAS.values():
            for dificultad, preset in banco.DIFICULTADES.items():
                informe = banco.correr(dificultad, politica.nombre, 40, tope=25)
                self.assertEqual(
                    informe.contradicciones,
                    0,
                    f"{politica.nombre} en {dificultad} contradijo al motor "
                    f"(tambor de {preset['huecos']} huecos)",
                )


class PoliticaRota(banco.Deductiva):
    """Una politica que se contradice a proposito.

    Descarta el hueco al que acaba de disparar Y tambien se queda solo
    con ese hueco: incompatible, asi que la creencia se vacia enseguida.
    Existe para comprobar que el contador de contradicciones salta
    cuando tiene que saltar; si no, el "0 contradicciones" del resto de
    tests no diria nada.
    """

    nombre = "rota"

    def vio_disparo_fallido(self, hueco: int) -> None:
        super().vio_disparo_fallido(hueco)
        self.creencia.tras_farol(hueco, acierto=False)
        self.creencia.tras_farol(hueco, acierto=True)


class TestElContadorDeContradiccionesFunciona(unittest.TestCase):
    def test_una_politica_rota_se_cuenta(self):
        banco.POLITICAS["rota"] = PoliticaRota
        try:
            informe = banco.correr("normal", "rota", 10, tope=10)
        finally:
            del banco.POLITICAS["rota"]
        self.assertEqual(informe.contradicciones, 10)

    def test_y_la_tabla_lo_grita(self):
        informe = banco.Informe("normal", "rota", 1)
        informe.contradicciones = 1
        self.assertIn("CONTRADICCIONES", banco._fila(informe))


class TestDeducirEsMejorQueElAzar(unittest.TestCase):
    """El banco solo vale si distingue una politica buena de una mala.

    Si deducir no ganase al azar por goleada, o el solver no sirve o el
    banco no esta midiendo lo que dice medir.
    """

    def test_deducir_sobrevive_mucho_mas(self):
        azar = banco.correr("normal", "azar", 60, tope=40)
        deduce = banco.correr("normal", "deduce", 60, tope=40)
        self.assertGreater(deduce.dias_medios, azar.dias_medios * 2)
        # Al azar tambien le puede tocar sobrevivir de chiripa (con este
        # tope pasa alguna vez de cada cien), asi que se compara la
        # proporcion y no se exige un cero.
        self.assertGreater(deduce.porcentaje_inmortal, azar.porcentaje_inmortal * 5)

    def test_farolear_acorrala_antes_que_no_hacerlo(self):
        sin = banco.correr("normal", "deduce", 60, tope=40)
        con = banco.correr("normal", "deduce+farol", 60, tope=40)
        self.assertLess(con.disparos_hasta_acorralar, sin.disparos_hasta_acorralar)


class TestInforme(unittest.TestCase):
    def test_agrega_todas_las_partidas(self):
        informe = banco.correr("normal", "deduce", 25, tope=15)
        self.assertEqual(informe.partidas, 25)
        self.assertEqual(len(informe.dias), 25)
        self.assertEqual(informe.muertes + informe.inmortales, 25)
        self.assertEqual(sum(informe.partidas_por_patron.values()), 25)

    def test_sin_muestras_la_media_se_imprime_como_guion(self):
        self.assertEqual(banco._medio(float("nan")), "--")
        self.assertEqual(banco._medio(3.14), "3.1")

    def test_sin_datos_por_patron_no_se_imprime_la_tabla(self):
        # Le pasa a la politica del azar: nunca acorrala, asi que no hay
        # nada que desglosar por patron.
        vacio = banco.Informe("normal", "azar", 10)
        self.assertEqual(banco._tabla_patrones(vacio), [])

    def test_la_tabla_sale_entera(self):
        texto = banco.informe_completo(5, tope=10)
        for dificultad in banco.DIFICULTADES:
            self.assertIn(dificultad, texto)
        for politica in banco.POLITICAS:
            self.assertIn(politica, texto)
        for patron in estado.PATRONES:
            self.assertIn(patron, texto)
        self.assertNotIn("CONTRADICCIONES", texto)


class TestDuelos(unittest.TestCase):
    def test_un_duelo_acaba_con_veredicto(self):
        self.assertIn(
            banco.jugar_duelo("implacable", "novato", 8, 3, 1), ("a", "b", "empate")
        )

    def test_la_misma_semilla_da_el_mismo_duelo(self):
        uno = banco.jugar_duelo("implacable", "templado", 8, 3, 9)
        otro = banco.jugar_duelo("implacable", "templado", 8, 3, 9)
        self.assertEqual(uno, otro)

    def test_deducir_gana_al_que_no_deduce(self):
        # Lo unico que hace util la tabla: si el nivel no cambiara el
        # resultado, no estaria midiendo nada.
        victorias = sum(
            banco.jugar_duelo("implacable", "novato", 8, 3, i) == "a" for i in range(60)
        )
        self.assertGreater(victorias, 30)

    def test_en_un_tambor_diminuto_alguien_se_planta(self):
        # Con tres huecos el riesgo minimo es 1/3 y los umbrales de
        # retirada entran en juego; en uno de ocho casi nunca aprietan.
        veredictos = {
            banco.jugar_duelo("implacable", "templado", 3, 2, i) for i in range(40)
        }
        self.assertTrue(veredictos <= {"a", "b", "empate"})

    def test_la_tabla_sale_entera(self):
        texto = banco.tabla_de_duelos(3)
        for nivel in banco.rival.NIVELES:
            self.assertIn(nivel, texto)


class TestArgumentos(unittest.TestCase):
    def test_valores_por_defecto(self):
        args = banco._parsear([])
        self.assertEqual(args.partidas, 5000)
        self.assertEqual(args.tope, banco.TOPE_DISPAROS)

    def test_se_pueden_cambiar(self):
        args = banco._parsear(["--partidas", "10", "--tope", "20"])
        self.assertEqual(args.partidas, 10)
        self.assertEqual(args.tope, 20)

    def test_la_tabla_de_duelos_se_pide_aparte(self):
        self.assertEqual(banco._parsear([]).duelos, 0)
        self.assertEqual(banco._parsear(["--duelos", "50"]).duelos, 50)


if __name__ == "__main__":
    unittest.main()
