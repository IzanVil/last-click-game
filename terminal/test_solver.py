import unittest

import estado
import motor
import pistas
import semillas
import solver


class TestCreenciaInicial(unittest.TestCase):
    def test_arranca_con_todas_las_combinaciones(self):
        creencia = solver.Creencia(8)
        self.assertEqual(len(creencia), 8 * len(estado.PATRONES))
        self.assertEqual(creencia.patrones_posibles(), set(estado.PATRONES))
        self.assertEqual(creencia.posiciones_posibles(), set(range(1, 9)))

    def test_el_riesgo_esta_repartido_y_suma_uno(self):
        riesgos = solver.Creencia(8).riesgo_por_hueco()
        self.assertEqual(len(riesgos), 8)
        self.assertAlmostEqual(sum(riesgos.values()), 1.0)
        self.assertAlmostEqual(riesgos[1], 1 / 8)


class TestActualizaciones(unittest.TestCase):
    def test_un_disparo_fallido_descarta_el_hueco_y_mueve(self):
        creencia = solver.Creencia(8, patrones=("avanza",))
        creencia.tras_disparo_fallido(3)
        # Sin el 3, y todo adelantado un paso: el 4 deja de ser posible
        # porque solo se llegaba a el desde el 3.
        self.assertNotIn(4, creencia.posiciones_posibles())
        self.assertIn(5, creencia.posiciones_posibles())

    def test_una_pista_veraz_deja_solo_sus_candidatos(self):
        creencia = solver.Creencia(8)
        creencia.tras_pista(frozenset({2, 4, 6, 8}))
        self.assertEqual(creencia.posiciones_posibles(), {2, 4, 6, 8})

    def test_una_pista_mentirosa_deja_justo_lo_contrario(self):
        creencia = solver.Creencia(8)
        creencia.tras_pista(frozenset({2, 4, 6, 8}), mentira=True)
        self.assertEqual(creencia.posiciones_posibles(), {1, 3, 5, 7})

    def test_el_clic_metalico_mueve_sin_descartar(self):
        creencia = solver.Creencia(8, patrones=("avanza",))
        antes = len(creencia)
        creencia.tras_clic_metalico()
        self.assertEqual(len(creencia), antes)
        self.assertEqual(creencia.posiciones_posibles(), set(range(1, 9)))

    def test_un_farol_acertado_tacha_ese_hueco(self):
        creencia = solver.Creencia(8)
        creencia.tras_farol(5, acierto=True)
        self.assertNotIn(5, creencia.posiciones_posibles())

    def test_un_farol_fallido_clava_la_posicion(self):
        # Fallar un farol es malo para el bolsillo y buenisimo para la
        # deduccion: dice exactamente donde esta la bala.
        creencia = solver.Creencia(8)
        creencia.tras_farol(5, acierto=False)
        self.assertEqual(creencia.posiciones_posibles(), {5})
        self.assertTrue(creencia.acorralada())


class TestElecciones(unittest.TestCase):
    def test_dispara_al_hueco_menos_probable(self):
        creencia = solver.Creencia(8)
        creencia.tras_pista(frozenset({2, 4, 6, 8}))
        self.assertIn(creencia.hueco_mas_seguro(), {1, 3, 5, 7})

    def test_farolea_el_hueco_mas_probable(self):
        creencia = solver.Creencia(8)
        creencia.tras_pista(frozenset({2, 4}))
        self.assertIn(creencia.hueco_mas_probable(), {2, 4})

    def test_los_empates_se_rompen_siempre_igual(self):
        # Da igual cual se elija, pero elegir siempre el mismo es lo que
        # permite que dos politicas jueguen el mismo tambor.
        uno = solver.Creencia(8).hueco_mas_seguro()
        otro = solver.Creencia(8).hueco_mas_seguro()
        self.assertEqual(uno, otro)

    def test_los_empatados_a_riesgo_minimo_salen_todos(self):
        creencia = solver.Creencia(8)
        creencia.tras_pista(frozenset({2, 4}))
        # Todo lo que no sea 2 ni 4 esta a riesgo cero y empata.
        self.assertEqual(creencia.huecos_mas_seguros(), [1, 3, 5, 6, 7, 8])

    def test_una_creencia_vacia_no_devuelve_ningun_hueco_seguro(self):
        creencia = solver.Creencia(8)
        creencia.tras_pista(frozenset())
        self.assertEqual(creencia.huecos_mas_seguros(), [])

    def test_una_creencia_vacia_no_revienta_al_elegir(self):
        creencia = solver.Creencia(8)
        creencia.tras_pista(frozenset())
        self.assertTrue(creencia.contradictoria())
        self.assertEqual(creencia.riesgo_por_hueco(), {})
        creencia.hueco_mas_seguro()
        creencia.hueco_mas_probable()


class TestContraElMotor(unittest.TestCase):
    """El test que de verdad importa: jugar y comprobar la deduccion.

    Despues de cada observacion, el estado REAL del tambor (su patron y
    donde esta la bala ahora) tiene que seguir entre los que la creencia
    da por posibles. Si alguna vez se cae, es que el solver entiende el
    juego de una forma distinta a como lo juega el motor -- y como la
    deduccion se escribio leyendo motor.disparar, eso vale tambien como
    comprobacion cruzada de las reglas.
    """

    def _jugar_comprobando(self, semilla, huecos=8, disparos_max=15):
        juego = motor.Motor(huecos=huecos, rng=semillas.generador(semilla))
        creencia = solver.Creencia(huecos)
        verdad = (juego.tambor.patron, juego.tambor.posicion_bala)
        self.assertIn(verdad, creencia.estados, "la creencia inicial no lo cubre todo")

        for _ in range(disparos_max):
            if juego.terminada:
                break
            hueco = creencia.hueco_mas_seguro()
            sucesos = juego.disparar(hueco)
            if any(isinstance(s, motor.Impacto) for s in sucesos):
                break

            creencia.tras_disparo_fallido(hueco)
            miente = any(
                isinstance(s, motor.EventoTambor) and s.tipo == "tambor_caliente"
                for s in sucesos
            )
            for suceso in sucesos:
                if isinstance(suceso, motor.EventoTambor):
                    if suceso.tipo == "clic_metalico":
                        creencia.tras_clic_metalico()
                elif isinstance(suceso, motor.PistaNueva):
                    creencia.tras_pista(suceso.pista.candidatos, miente)

            verdad = (juego.tambor.patron, juego.tambor.posicion_bala)
            self.assertFalse(
                creencia.contradictoria(), f"creencia vacia (semilla {semilla})"
            )
            self.assertIn(
                verdad,
                creencia.estados,
                f"la creencia descarto la verdad {verdad} (semilla {semilla})",
            )

    def test_la_verdad_nunca_se_queda_fuera(self):
        for semilla in range(120):
            self._jugar_comprobando(semilla)

    def test_tambien_con_tambores_de_otro_tamano(self):
        for semilla in range(40):
            self._jugar_comprobando(semilla, huecos=6)
            self._jugar_comprobando(semilla, huecos=10)


class TestPistasMentirosasDeVerdad(unittest.TestCase):
    def test_el_complemento_de_una_mentira_cubre_la_posicion_real(self):
        # Se generan pistas mentirosas de verdad (no a mano) para cada
        # tipo y posicion, y se comprueba que quedarse con lo contrario
        # nunca descarta donde esta la bala.
        for huecos in (6, 8, 10):
            for posicion in range(1, huecos + 1):
                for ultimo in [None, *range(1, huecos + 1)]:
                    for tipo in pistas.TIPOS_PISTA:
                        if tipo == "relativa" and ultimo is None:
                            continue
                        pista = pistas.generar_pista(
                            posicion, huecos, ultimo, tipo=tipo, mentir=True
                        )
                        self.assertNotIn(
                            posicion,
                            pista.candidatos,
                            f"{tipo} mentirosa incluye la posicion real "
                            f"({posicion}/{huecos}, ultimo={ultimo})",
                        )


if __name__ == "__main__":
    unittest.main()
