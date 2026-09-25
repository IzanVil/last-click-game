import unittest
from unittest.mock import patch

import estado
import motor


def _tipos(sucesos):
    """Los nombres de los sucesos devueltos, en orden."""
    return [type(s).__name__ for s in sucesos]


def _primero(sucesos, clase):
    for suceso in sucesos:
        if isinstance(suceso, clase):
            return suceso
    return None


def _motor_fijo(patron="avanza", posicion=8, **kwargs):
    """Un motor con el tambor puesto a mano y sin eventos aleatorios.

    Los eventos se apagan (probabilidad 0) porque un "clic_metalico"
    mueve la bala un paso de mas y haria intermitentes las secuencias
    fijas de disparos de abajo; los que si quieren evento lo fuerzan
    parcheando tirar_evento.
    """
    kwargs.setdefault("probabilidad_eventos", 0.0)
    juego = motor.Motor(**kwargs)
    juego.tambor = estado.TamborJuicio(
        huecos=juego.huecos, patron=patron, posicion_inicial=posicion
    )
    return juego


class TestDisparo(unittest.TestCase):
    def test_hueco_fuera_del_tambor_no_gasta_nada(self):
        juego = _motor_fijo()
        sucesos = juego.disparar(99)
        self.assertEqual(_tipos(sucesos), ["EntradaInvalida"])
        self.assertEqual(juego.disparos, 0)
        self.assertFalse(juego.terminada)

    def test_sobrevivir_dobla_la_apuesta_y_deja_una_pista(self):
        juego = _motor_fijo()
        sucesos = juego.disparar(1)
        self.assertEqual(_tipos(sucesos), ["DisparoSobrevivido", "PistaNueva"])
        self.assertEqual(juego.apuesta.en_juego, 200)
        self.assertEqual(len(juego.pistas_reveladas), 1)
        self.assertEqual(_primero(sucesos, motor.PistaNueva).numero, 1)

    def test_el_impacto_termina_la_partida_y_se_lo_lleva_todo(self):
        juego = _motor_fijo(posicion=3)
        sucesos = juego.disparar(3)
        self.assertEqual(_tipos(sucesos), ["Impacto"])
        impacto = sucesos[0]
        self.assertEqual(impacto.perdidos, 100)
        self.assertEqual(juego.apuesta.en_juego, 0)
        self.assertTrue(juego.terminada)

    def test_el_disparo_que_te_mata_no_cuenta_como_dia_sobrevivido(self):
        # Tres disparos son un dia, pero solo si se sobrevive a los tres.
        # `disparos` sigue contando el tiro fatal -- se apreto el gatillo
        # y la pantalla final dice "caiste tras 3 disparo(s)" -- pero ese
        # no se sobrevivio.
        # "espejo" manda la bala a 9-posicion, asi que rebota entre el 3
        # y el 6: falla los dos primeros tiros y vuelve al 3 para el
        # tercero.
        juego = _motor_fijo(patron="espejo", posicion=3)
        juego.disparar(1)
        juego.disparar(2)
        impacto = juego.disparar(3)[0]
        self.assertIsInstance(impacto, motor.Impacto)
        self.assertEqual(impacto.disparos, 3)
        self.assertEqual(impacto.dias, 0)
        self.assertEqual(juego.jugadores[0].dias, 0)

    def test_tres_disparos_sobrevividos_completan_un_dia(self):
        juego = _motor_fijo()
        self.assertNotIn("DiaCompletado", _tipos(juego.disparar(1)))
        self.assertNotIn("DiaCompletado", _tipos(juego.disparar(2)))
        sucesos = juego.disparar(3)
        self.assertEqual(_primero(sucesos, motor.DiaCompletado).dia, 1)
        self.assertEqual(juego.apuesta.en_juego, 800)

    def test_el_orden_de_los_sucesos_es_el_cronologico(self):
        # Sobrevives, el tambor hace de las suyas, llega la pista y
        # se cierra el dia. La interfaz se fia de este orden para
        # pintarlo tal cual, sin reordenar nada.
        juego = _motor_fijo()
        juego.disparar(1)
        juego.disparar(2)
        with patch("motor.eventos.tirar_evento", return_value="tambor_caliente"):
            sucesos = juego.disparar(3)
        self.assertEqual(
            _tipos(sucesos),
            ["DisparoSobrevivido", "EventoTambor", "PistaNueva", "DiaCompletado"],
        )


class TestEventos(unittest.TestCase):
    def test_el_clic_metalico_mueve_la_bala_un_paso_de_mas(self):
        juego = _motor_fijo(posicion=8)
        with patch("motor.eventos.tirar_evento", return_value="clic_metalico"):
            juego.disparar(1)
        # Disparo fallido: 8 -> 1. Y el clic metalico: 1 -> 2.
        self.assertEqual(juego.tambor.posicion_bala, 2)

    def test_el_tambor_caliente_pide_una_pista_mentirosa(self):
        juego = _motor_fijo()
        with (
            patch("motor.eventos.tirar_evento", return_value="tambor_caliente"),
            patch("motor.pistas.generar_pista") as mock_pista,
        ):
            juego.disparar(1)
        self.assertTrue(mock_pista.call_args.kwargs["mentir"])

    def test_los_eventos_cuentan_para_el_resumen_final(self):
        juego = _motor_fijo()
        with patch("motor.eventos.tirar_evento", return_value="clic_metalico"):
            juego.disparar(1)
        self.assertEqual(juego.bitacora.eventos, {"clic_metalico": 1})


class TestFarol(unittest.TestCase):
    def test_acertar_suma_bono_sin_tocar_la_bala(self):
        juego = _motor_fijo(posicion=5)
        sucesos = juego.marcar(2)
        resuelto = sucesos[0]
        self.assertTrue(resuelto.acierto)
        self.assertEqual(resuelto.bono, motor.BONO_MARCA_ACERTADA)
        self.assertEqual(juego.apuesta.en_juego, 150)
        self.assertEqual(juego.tambor.posicion_bala, 5)
        self.assertEqual(juego.marca.marcas_restantes, 2)

    def test_fallar_gasta_la_marca_y_no_da_nada(self):
        juego = _motor_fijo(posicion=5)
        resuelto = juego.marcar(5)[0]
        self.assertFalse(resuelto.acierto)
        self.assertEqual(resuelto.bono, 0)
        self.assertEqual(juego.apuesta.en_juego, 100)
        self.assertEqual(juego.marca.marcas_restantes, 2)

    def test_marcar_nunca_termina_la_partida(self):
        juego = _motor_fijo(posicion=5)
        juego.marcar(5)
        self.assertFalse(juego.terminada)

    def test_hueco_fuera_del_tambor_no_gasta_marca(self):
        juego = _motor_fijo()
        self.assertEqual(_tipos(juego.marcar(0)), ["EntradaInvalida"])
        self.assertEqual(juego.marca.marcas_restantes, 3)


class TestRetirada(unittest.TestCase):
    def test_cobra_lo_que_hay_en_juego(self):
        juego = _motor_fijo()
        juego.disparar(1)
        retirada = juego.retirarse()[0]
        self.assertEqual(retirada.ganados, 200)
        self.assertEqual(retirada.disparos, 1)
        self.assertTrue(juego.terminada)


class TestDuelo(unittest.TestCase):
    def test_solitario_no_es_duelo_pero_tiene_un_jugador(self):
        juego = _motor_fijo()
        self.assertFalse(juego.es_duelo())
        self.assertEqual(len(juego.jugadores), 1)

    def test_el_turno_cambia_tras_disparar_y_tras_marcar(self):
        juego = _motor_fijo(nombres=["Ana", "Bea"])
        cambio = _primero(juego.disparar(1), motor.TurnoCambiado)
        self.assertEqual(cambio.nombre, "Bea")
        self.assertEqual(cambio.rival_nombre, "Ana")
        cambio = _primero(juego.marcar(1), motor.TurnoCambiado)
        self.assertEqual(cambio.nombre, "Ana")

    def test_cada_jugador_tiene_su_apuesta_y_sus_marcas(self):
        juego = _motor_fijo(nombres=["Ana", "Bea"])
        juego.disparar(1)  # Ana sobrevive: su apuesta se dobla
        self.assertEqual(juego.jugadores[0].apuesta.en_juego, 200)
        self.assertEqual(juego.jugadores[1].apuesta.en_juego, 100)

    def test_el_tambor_y_las_pistas_son_compartidos(self):
        juego = _motor_fijo(nombres=["Ana", "Bea"])
        juego.disparar(1)
        juego.disparar(2)
        self.assertEqual(len(juego.pistas_reveladas), 2)
        self.assertEqual(juego.marcadas(), {1, 2})

    def test_el_duelo_acaba_al_caer_uno_y_el_rival_conserva_lo_suyo(self):
        juego = _motor_fijo(posicion=8, nombres=["Ana", "Bea"])
        juego.disparar(1)  # Ana sobrevive (bala 8 -> 1), apuesta 200
        sucesos = juego.disparar(1)  # Bea dispara donde ahora esta la bala
        self.assertEqual(_tipos(sucesos), ["Impacto", "DueloTerminado"])
        terminado = sucesos[1]
        self.assertEqual(juego.jugadores[1].puntos_finales, 0)
        self.assertEqual(juego.jugadores[1].apuesta.en_juego, 0)
        self.assertEqual(juego.jugadores[0].puntos_finales, 200)
        self.assertEqual([g.nombre for g in terminado.ganadores], ["Ana"])

    def test_el_suceso_de_impacto_sigue_diciendo_cuanto_se_perdio(self):
        # Con lo que se TERMINA es con nada, pero la pantalla final tiene
        # que poder decir "perdiendo 200 puntos": eso va en el suceso.
        juego = _motor_fijo(posicion=8)
        juego.disparar(1)  # sobrevive y dobla a 200
        impacto = juego.disparar(1)[0]
        self.assertEqual(impacto.perdidos, 200)
        self.assertEqual(juego.jugadores[0].puntos_finales, 0)


if __name__ == "__main__":
    unittest.main()
