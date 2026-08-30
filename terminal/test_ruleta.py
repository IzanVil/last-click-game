import unittest
from functools import partial
from unittest.mock import patch

import ambiente
import apuestas
import efectos
import eventos
import farol
import historial
import pistas
import records
import ruleta

# Parche vivo mientras corre este modulo de tests (ver setUpModule).
_parche_teclado: object = None


def setUpModule() -> None:
    """Deja la interfaz muda antes de tocarla.

    Sin animaciones nada duerme ni escribe codigos de escape en la
    terminal de quien lanza los tests (es el mismo interruptor que
    --sin-animaciones), y con el teclado en crudo desactivado el
    selector cae al metodo de teclear, que es el que los tests
    alimentan con `input`. Ojo: `sys.stdin` SI es una terminal cuando
    los tests se lanzan a mano, asi que sin este parche el selector se
    quedaria esperando una flecha que nunca llega.
    """
    global _parche_teclado
    efectos.configurar(animaciones=False, sonido=False)
    _parche_teclado = patch("entrada.modo_tecla_disponible", return_value=False)
    _parche_teclado.start()


def tearDownModule() -> None:
    _parche_teclado.stop()


class FakeTambor:
    """Doble de estado.TamborJuicio con resultados de disparo prefijados."""

    def __init__(self, resultados, huecos=8, posicion_bala=5):
        self.huecos = huecos
        self.posicion_bala = posicion_bala
        self.ultimo_disparo = None
        self.historial = []
        self._resultados = iter(resultados)
        self.movimientos_extra = 0

    def disparar(self, numero):
        self.ultimo_disparo = numero
        self.historial.append(numero)
        return next(self._resultados)

    def mover_extra(self):
        self.movimientos_extra += 1
        self.posicion_bala += 1  # desplazamiento simbolico para el test
        return self.posicion_bala


def _comprobar_final(caso, mock_pantalla, esperado):
    """Comprueba una llamada a impacto()/retirada() desde el bucle.

    Los cinco primeros argumentos (disparos, puntos, dias, resumen y si
    hay record) se comparan uno a uno; el sexto solo se mira que sea un
    Epilogo, porque cual toca ya lo cubren los tests de ambiente.py y
    fijarlo aqui ataria estos tests al texto de cada final.
    """
    mock_pantalla.assert_called_once()
    llamada = mock_pantalla.call_args
    caso.assertEqual(llamada.args[: len(esperado)], esperado)
    caso.assertIsInstance(llamada.args[len(esperado)], ambiente.Epilogo)


def _parchear_records(func):
    """Decorador que evita que los tests toquen el archivo de records real
    del usuario: jugar()/jugar_duelo() cargan y guardan records siempre,
    asi que cualquier test que las llame necesita este doble parcheo."""
    func = patch("ruleta.records.guardar")(func)
    func = patch("ruleta.records.cargar", return_value=records.Records())(func)
    return func


class TestCalcularEstados(unittest.TestCase):
    def test_candidato_por_defecto(self):
        estados = ruleta.calcular_estados(set(), {}, frozenset({2, 4}))
        self.assertEqual(estados, {2: "candidato", 4: "candidato"})

    def test_probado_pisa_a_candidato(self):
        estados = ruleta.calcular_estados({2}, {}, frozenset({2, 4}))
        self.assertEqual(estados[2], "probado")
        self.assertEqual(estados[4], "candidato")

    def test_resultado_de_farol_pisa_a_todo_lo_demas(self):
        estados = ruleta.calcular_estados({3}, {3: "seguro"}, frozenset({3}))
        self.assertEqual(estados[3], "seguro")


class TestDibujarTambor(unittest.TestCase):
    def test_pinta_cada_estado_con_su_glifo(self):
        estados = {1: "seguro", 2: "peligro", 3: "candidato", 4: "probado"}
        with patch("builtins.print") as mock_print:
            ruleta.dibujar_tambor(estados, huecos=4)

        filas = [str(llamada.args[0]) for llamada in mock_print.call_args_list]
        fila_celdas = filas[1]
        self.assertIn("✓", fila_celdas)
        self.assertIn("✗", fila_celdas)
        self.assertIn("?", fila_celdas)
        self.assertIn("·", fila_celdas)


class TestElegirAccion(unittest.TestCase):
    def test_acepta_disparar(self):
        with patch("builtins.input", return_value="d"):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=3), "disparar")

    def test_acepta_retirarse(self):
        with patch("builtins.input", return_value="R"):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=3), "retirarse")

    def test_acepta_marcar_si_quedan_marcas(self):
        with patch("builtins.input", return_value="m"):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=1), "marcar")

    def test_rechaza_marcar_sin_marcas_disponibles(self):
        entradas = iter(["m", "d"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=0), "disparar")

    def test_rechaza_entrada_invalida(self):
        entradas = iter(["x", "disparar"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            self.assertEqual(ruleta.elegir_accion(marcas_restantes=3), "disparar")


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
    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_sobrevive_y_se_retira_con_la_apuesta_doblada(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([False])

        entradas = iter(["d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        # 1 disparo sobrevivido -> 0 dias completos (hacen falta 3), sin
        # faroles ni eventos en el resumen, y sin record (no hay ninguno
        # previo que batir por encima de 0 dias).
        _comprobar_final(
            self,
            mock_retirada,
            (1, 200, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos.", False),
        )
        mock_guardar.assert_called_once()

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.impacto")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_impacto_pierde_todo_lo_apostado(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_impacto,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([False, True])

        entradas = iter(["d", "3", "d", "4", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        _comprobar_final(
            self,
            mock_impacto,
            (2, 200, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos.", False),
        )

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_marcar_acertado_suma_bono_sin_disparar(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        # posicion_bala=5 por defecto: marcar el 3 acierta (no es la bala).
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([])

        entradas = iter(["m", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        # Marcar no cuenta como disparo (0) y suma el bono sin doblar:
        # 100 + 50 = 150. El resumen refleja el farol acertado.
        _comprobar_final(
            self,
            mock_retirada,
            (
                0,
                150,
                0,
                "Hoy sobreviviste 0 dias y faroleaste 1 vez (1 acertado).",
                False,
            ),
        )

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_marcar_fallido_pierde_la_marca_sin_tocar_los_puntos(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        # posicion_bala=5 por defecto: marcar justo el 5 falla.
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([])

        entradas = iter(["m", "5", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        _comprobar_final(
            self,
            mock_retirada,
            (
                0,
                100,
                0,
                "Hoy sobreviviste 0 dias y faroleaste 1 vez (0 acertados).",
                False,
            ),
        )

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value="clic_metalico")
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_evento_clic_metalico_mueve_la_bala_otra_vez(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        fake = FakeTambor([False])
        mock_tambor_cls.side_effect = lambda huecos=None: fake

        entradas = iter(["d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        self.assertEqual(fake.movimientos_extra, 1)

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value="tambor_caliente")
    @patch("ruleta.pistas.generar_pista")
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_evento_tambor_caliente_pide_una_pista_mentirosa(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_generar_pista,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([False])
        mock_generar_pista.return_value = pistas.Pista(
            "pista falsa", frozenset({1, 2, 3})
        )

        entradas = iter(["d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        self.assertTrue(mock_generar_pista.call_args.kwargs["mentir"])

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_completa_un_dia_cada_tres_disparos_sobrevividos(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor(
            [False, False, False]
        )

        entradas = iter(["d", "1", "d", "2", "d", "3", "r", "n"])
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        # 3 disparos sobrevividos (100 -> 200 -> 400 -> 800) = 1 dia
        # completo, y como no habia ningun record previo (0 dias), este
        # se marca como nuevo record.
        dias, ganados, disparos = 1, 800, 3
        llamada = mock_retirada.call_args
        self.assertEqual(llamada.args[:3], (disparos, ganados, dias))
        self.assertIn("sobreviviste 1 dia", llamada.args[3])
        self.assertTrue(llamada.args[4])

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_impacto_muestra_boom_lo_perdido_y_el_resumen(
        self, mock_limpiar, mock_sleep
    ):
        with patch("builtins.print") as mock_print:
            ruleta.impacto(2, 200, 0, "Hoy sobreviviste 0 dias.")

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        # Se comprueba el contenido real (BOOM, los puntos perdidos y el
        # resumen), no el color exacto ni el espaciado entre letras.
        self.assertRegex(mensajes, r"(?i)b\s*o\s*o\s*m")
        self.assertIn("200", mensajes)
        self.assertIn("Hoy sobreviviste 0 dias.", mensajes)
        self.assertNotIn("record", mensajes.lower())

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_impacto_anuncia_nuevo_record(self, mock_limpiar, mock_sleep):
        with patch("builtins.print") as mock_print:
            ruleta.impacto(2, 200, 5, "Hoy sobreviviste 5 dias.", nuevo_record=True)

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("Nuevo record", mensajes)

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_pantalla_retirada_muestra_lo_cobrado_y_el_resumen(
        self, mock_limpiar, mock_sleep
    ):
        with patch("builtins.print") as mock_print:
            ruleta.retirada(3, 400, 1, "Hoy sobreviviste 1 dia.")

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("400", mensajes)
        self.assertIn("Hoy sobreviviste 1 dia.", mensajes)
        self.assertNotIn("record", mensajes.lower())


class TestJugadorDuelo(unittest.TestCase):
    def test_dias_se_deriva_de_los_disparos(self):
        jugador = ruleta.JugadorDuelo("Ana", apuestas.Apuesta(100), farol.Farol())
        jugador.disparos = 7
        self.assertEqual(jugador.dias, 2)


class TestResultadoDuelo(unittest.TestCase):
    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_gana_quien_sobrevive_mas_dias(self, mock_limpiar, mock_sleep):
        ana = ruleta.JugadorDuelo("Ana", apuestas.Apuesta(100), farol.Farol())
        ana.disparos, ana.puntos_finales = 6, 300  # 2 dias
        beto = ruleta.JugadorDuelo("Beto", apuestas.Apuesta(100), farol.Farol())
        beto.disparos, beto.puntos_finales = 3, 900  # 1 dia, pero mas puntos

        with (
            patch("builtins.input", return_value=""),
            patch("builtins.print") as mock_print,
        ):
            ruleta.resultado_duelo([ana, beto])

        mensajes = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertIn("Gana Ana", mensajes)

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_empate_en_dias_lo_desempata_los_puntos(self, mock_limpiar, mock_sleep):
        ana = ruleta.JugadorDuelo("Ana", apuestas.Apuesta(100), farol.Farol())
        ana.disparos, ana.puntos_finales = 3, 400
        beto = ruleta.JugadorDuelo("Beto", apuestas.Apuesta(100), farol.Farol())
        beto.disparos, beto.puntos_finales = 3, 900

        with (
            patch("builtins.input", return_value=""),
            patch("builtins.print") as mock_print,
        ):
            ruleta.resultado_duelo([ana, beto])

        mensajes = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertIn("Gana Beto", mensajes)

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    def test_empate_total(self, mock_limpiar, mock_sleep):
        ana = ruleta.JugadorDuelo("Ana", apuestas.Apuesta(100), farol.Farol())
        ana.disparos, ana.puntos_finales = 3, 400
        beto = ruleta.JugadorDuelo("Beto", apuestas.Apuesta(100), farol.Farol())
        beto.disparos, beto.puntos_finales = 3, 400

        with (
            patch("builtins.input", return_value=""),
            patch("builtins.print") as mock_print,
        ):
            ruleta.resultado_duelo([ana, beto])

        mensajes = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertIn("Empate", mensajes)


class TestJugarDuelo(unittest.TestCase):
    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_turnos_alternan_y_el_duelo_acaba_al_retirarse_el_activo(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        # posicion_bala=5 por defecto (nunca coincide con los disparos de
        # abajo): dos disparos sobreviven, uno por jugador, y el turno
        # vuelve al primer jugador, que se retira.
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([False, False])

        entradas = iter(
            [
                "",  # nombre jugador 1 (por defecto)
                "",  # nombre jugador 2 (por defecto)
                "d",
                "3",  # turno 1: Jugador 1 dispara y sobrevive
                "d",
                "4",  # turno 2: Jugador 2 dispara y sobrevive
                "r",  # turno 3: Jugador 1 se retira -> fin del duelo
                "",  # "Pulsa Enter para continuar" del resultado
                "n",  # no jugar otro duelo
            ]
        )
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("ruleta.retirada") as mock_retirada,
            patch("builtins.print") as mock_print,
        ):
            ruleta.jugar_duelo()

        # Jugador 1: 1 disparo sobrevivido (100 -> 200) y se retira con
        # esos 200 puntos; 0 dias (hacen falta 3 disparos).
        _comprobar_final(
            self,
            mock_retirada,
            (1, 200, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos.", False),
        )

        # Jugador 2 tambien habia doblado su apuesta a 200 en su unico
        # turno; al no retirarse ni morir, sus "puntos finales" son los
        # que tenia en juego cuando el duelo termino.
        mensajes = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertIn("Jugador 2: 0 dia(s) sobrevividos, 200 puntos", mensajes)
        # Con los mismos dias (0) y los mismos puntos (200 cada uno),
        # el duelo termina en empate.
        self.assertIn("Empate", mensajes)

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_marcar_en_duelo_suma_bono_y_congela_los_puntos_del_rival(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        # posicion_bala=5 por defecto: marcar el 3 acierta (no es la bala).
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([])

        entradas = iter(
            [
                "",
                "",  # nombres por defecto
                "m",
                "3",  # turno 1: Jugador 1 marca y acierta (+50 puntos)
                "r",  # turno 2: Jugador 2 se retira -> fin del duelo
                "",  # "Pulsa Enter para continuar" del resultado
                "n",
            ]
        )
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("ruleta.retirada") as mock_retirada,
            patch("builtins.print") as mock_print,
        ):
            ruleta.jugar_duelo()

        # Jugador 2 se retira sin haber hecho nada: cobra su apuesta base.
        _comprobar_final(
            self,
            mock_retirada,
            (0, 100, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos.", False),
        )

        # Jugador 1 no llego a retirarse ni a morir: sus puntos finales
        # quedan congelados en los 150 (100 + 50 de bono) que tenia en
        # juego, y eso es justo lo que le hace ganar el duelo.
        mensajes = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertIn("Jugador 1: 0 dia(s) sobrevividos, 150 puntos", mensajes)
        self.assertIn("Gana Jugador 1", mensajes)

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.eventos.tirar_evento", return_value=None)
    @patch("ruleta.impacto")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_impacto_en_duelo_termina_la_partida(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_impacto,
        mock_evento,
        mock_limpiar,
        mock_sleep,
    ):
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([False, True])

        entradas = iter(
            [
                "",
                "",  # nombres por defecto
                "d",
                "3",  # turno 1: Jugador 1 dispara y sobrevive (100 -> 200)
                "d",
                "5",  # turno 2: Jugador 2 dispara justo la bala -> BOOM
                "",  # "Pulsa Enter para continuar" del resultado
                "n",  # no jugar otro duelo
            ]
        )
        with (
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar_duelo()

        # Jugador 2 muere en su primer disparo: pierde su apuesta base
        # entera (nunca llego a doblarla).
        _comprobar_final(
            self,
            mock_impacto,
            (1, 100, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos.", False),
        )


class TestParsearArgs(unittest.TestCase):
    def test_valores_por_defecto_son_la_dificultad_normal(self):
        args = ruleta._parsear_args([])
        self.assertEqual(args.huecos, ruleta.estado.HUECOS)
        self.assertEqual(args.marcas, ruleta.farol.MARCAS_INICIALES)
        self.assertFalse(args.duelo)
        self.assertFalse(args.records)

    def test_dificultad_facil(self):
        args = ruleta._parsear_args(["--dificultad", "facil"])
        self.assertEqual(args.huecos, ruleta.DIFICULTADES["facil"]["huecos"])
        self.assertEqual(args.marcas, ruleta.DIFICULTADES["facil"]["marcas"])

    def test_dificultad_dificil(self):
        args = ruleta._parsear_args(["--dificultad", "dificil"])
        self.assertEqual(args.huecos, ruleta.DIFICULTADES["dificil"]["huecos"])
        self.assertEqual(args.marcas, ruleta.DIFICULTADES["dificil"]["marcas"])

    def test_huecos_y_marcas_explicitos_pisan_el_preset(self):
        args = ruleta._parsear_args(
            ["--dificultad", "facil", "--huecos", "5", "--marcas", "1"]
        )
        self.assertEqual(args.huecos, 5)
        self.assertEqual(args.marcas, 1)

    def test_acepta_huecos_personalizado(self):
        args = ruleta._parsear_args(["--huecos", "6"])
        self.assertEqual(args.huecos, 6)

    def test_rechaza_huecos_insuficiente(self):
        with self.assertRaises(SystemExit):
            ruleta._parsear_args(["--huecos", "1"])

    def test_rechaza_marcas_negativas(self):
        with self.assertRaises(SystemExit):
            ruleta._parsear_args(["--marcas", "-1"])

    def test_acepta_marcas_cero(self):
        args = ruleta._parsear_args(["--marcas", "0"])
        self.assertEqual(args.marcas, 0)

    def test_duelo(self):
        args = ruleta._parsear_args(["--duelo"])
        self.assertTrue(args.duelo)

    def test_records(self):
        args = ruleta._parsear_args(["--records"])
        self.assertTrue(args.records)

    def test_version_sale_con_exit_0_y_no_es_error(self):
        with self.assertRaises(SystemExit) as contexto:
            ruleta._parsear_args(["--version"])
        self.assertEqual(contexto.exception.code, 0)


class TestVersionTexto(unittest.TestCase):
    def test_version_instalada(self):
        with patch("ruleta.version", return_value="1.2.3"):
            self.assertEqual(ruleta._version_texto(), "1.2.3")

    def test_sin_instalar_no_revienta(self):
        with patch("ruleta.version", side_effect=ruleta.PackageNotFoundError):
            self.assertIn("sin instalar", ruleta._version_texto())


class TestMain(unittest.TestCase):
    def setUp(self):
        # main() vuelve a mostrar el cursor al salir, y eso escribe un
        # codigo de escape en la terminal de quien lanza los tests.
        parche = patch("ruleta.efectos.cursor")
        parche.start()
        self.addCleanup(parche.stop)

    def tearDown(self):
        # main() enciende o apaga los efectos segun los flags que reciba:
        # despues de cada test hay que volver a dejar la interfaz muda
        # para el resto del modulo (ver setUpModule).
        efectos.configurar(animaciones=False, sonido=False)

    @patch("ruleta.jugar")
    def test_pasa_huecos_y_marcas_a_jugar(self, mock_jugar):
        ruleta.main(["--huecos", "6", "--marcas", "2"])
        mock_jugar.assert_called_once_with(huecos=6, marcas=2, oscuridad=False)

    @patch("ruleta.jugar")
    def test_pasa_el_modo_oscuridad(self, mock_jugar):
        ruleta.main(["--oscuridad"])
        self.assertTrue(mock_jugar.call_args.kwargs["oscuridad"])

    @patch("ruleta.jugar")
    def test_sin_animaciones_y_sin_sonido_apagan_los_efectos(self, mock_jugar):
        ruleta.main(["--sin-animaciones", "--sin-sonido"])
        self.assertFalse(efectos.AJUSTES.animaciones)
        self.assertFalse(efectos.AJUSTES.sonido)

    @patch("ruleta.jugar")
    def test_por_defecto_las_animaciones_estan_encendidas(self, mock_jugar):
        ruleta.main([])
        self.assertTrue(efectos.AJUSTES.animaciones)

    @patch("ruleta.jugar_duelo")
    def test_duelo_llama_a_jugar_duelo_en_vez_de_jugar(self, mock_jugar_duelo):
        ruleta.main(["--duelo", "--huecos", "6"])
        mock_jugar_duelo.assert_called_once_with(
            huecos=6, marcas=farol.MARCAS_INICIALES, oscuridad=False
        )

    @patch("ruleta.jugar")
    @patch(
        "ruleta.records.cargar",
        return_value=records.Records(partidas_jugadas=1, dias_maximos=3),
    )
    def test_records_imprime_el_resumen_y_no_juega(self, mock_cargar, mock_jugar):
        with patch("builtins.print") as mock_print:
            ruleta.main(["--records"])

        mock_jugar.assert_not_called()
        mensajes = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertIn("3 dia(s)", mensajes)

    @patch("ruleta.jugar", side_effect=KeyboardInterrupt)
    def test_ctrl_c_sale_con_mensaje_sin_traceback(self, mock_jugar):
        with patch("builtins.print") as mock_print:
            ruleta.main([])  # no debe propagar la excepcion

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("Hasta la proxima", mensajes)

    @patch("ruleta.jugar")
    def test_sin_interrupcion_no_imprime_despedida(self, mock_jugar):
        with patch("builtins.print") as mock_print:
            ruleta.main([])

        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertNotIn("Hasta la proxima", mensajes)


class TestOscurecer(unittest.TestCase):
    def test_tapa_lo_que_no_se_ha_comprobado(self):
        estados = ruleta.oscurecer({2: "candidato"}, huecos=4)
        self.assertEqual(estados, {1: "oculto", 2: "oculto", 3: "oculto", 4: "oculto"})

    def test_deja_ver_lo_disparado_y_lo_faroleado(self):
        estados = ruleta.oscurecer(
            {1: "probado", 2: "seguro", 3: "peligro", 4: "candidato"}, huecos=4
        )
        self.assertEqual(
            estados,
            {1: "probado", 2: "seguro", 3: "peligro", 4: "oculto"},
        )


class TestTamborAscii(unittest.TestCase):
    def test_las_cuatro_filas_del_tambor_encajan(self):
        filas = ruleta.tambor_ascii({}, huecos=6).split("\n")
        self.assertEqual(len(filas), 4)
        anchos = {efectos.ancho_visible(fila) for fila in filas[:3]}
        self.assertEqual(len(anchos), 1)

    def test_cada_estado_lleva_su_glifo(self):
        dibujo = ruleta.tambor_ascii(
            {1: "seguro", 2: "peligro", 3: "candidato", 4: "probado", 5: "oculto"},
            huecos=5,
        )
        for glifo in ("✓", "✗", "?", "·", "▒"):
            self.assertIn(glifo, dibujo)

    def test_el_hueco_resaltado_sale_en_video_inverso(self):
        dibujo = ruleta.tambor_ascii({}, huecos=4, resaltado=3)
        self.assertIn(efectos.INVERSO, dibujo)
        self.assertNotIn(efectos.INVERSO, ruleta.tambor_ascii({}, huecos=4))

    def test_resaltar_no_cambia_el_ancho_de_la_fila(self):
        normal = ruleta.tambor_ascii({}, huecos=4).split("\n")[1]
        resaltada = ruleta.tambor_ascii({}, huecos=4, resaltado=2).split("\n")[1]
        self.assertEqual(
            efectos.ancho_visible(normal), efectos.ancho_visible(resaltada)
        )

    def test_la_alerta_tine_el_marco_de_rojo(self):
        self.assertIn(ruleta.ROJO, ruleta.tambor_ascii({}, huecos=4, alerta=True))
        self.assertNotIn(ruleta.ROJO, ruleta.tambor_ascii({}, huecos=4))


class TestPanelAcciones(unittest.TestCase):
    def test_siempre_ocupa_el_mismo_alto(self):
        vacia = historial.Historial()
        llena = historial.Historial()
        for numero in range(historial.MAX_ACCIONES + 3):
            llena.registrar_accion("disparo", f"accion {numero}")
        self.assertEqual(
            efectos.alto_de(ruleta.panel_acciones(vacia)),
            efectos.alto_de(ruleta.panel_acciones(llena)),
        )

    def test_muestra_las_ultimas_acciones_con_su_color(self):
        bitacora = historial.Historial()
        bitacora.registrar_accion("disparo", "Disparo al 3")
        bitacora.registrar_accion("aviso", "Farol en el 5: ahi estaba")
        panel = ruleta.panel_acciones(bitacora)
        self.assertIn("Disparo al 3", panel)
        self.assertIn(ruleta.COLORES_ACCION["aviso"], panel)


class TestBloqueTablero(unittest.TestCase):
    def _tablero(self):
        return ruleta.Tablero(4, {}, [], historial.Historial())

    def test_el_alto_no_cambia_con_la_alerta_ni_el_resaltado(self):
        tablero = self._tablero()
        alto_normal = efectos.alto_de(ruleta.bloque_tablero(tablero))
        tablero.resaltado = 2
        self.assertEqual(
            efectos.alto_de(ruleta.bloque_tablero(tablero, alerta=True)), alto_normal
        )


class TestRefrescar(unittest.TestCase):
    def test_repinta_con_animaciones(self):
        pintados = []
        efectos.AJUSTES.animaciones = True
        try:
            ruleta.refrescar(partial(pintados.append, "pintado"))
        finally:
            efectos.AJUSTES.animaciones = False
        self.assertEqual(pintados, ["pintado"])

    def test_no_repite_el_tablero_sin_animaciones(self):
        pintados = []
        ruleta.refrescar(partial(pintados.append, "pintado"))
        self.assertEqual(pintados, [])


class TestBalaCerca(unittest.TestCase):
    def test_con_el_tambor_entero_por_probar_no_hay_tension(self):
        self.assertFalse(ruleta.bala_cerca(set(), huecos=8))

    def test_al_quedar_pocos_huecos_el_tambor_late(self):
        self.assertTrue(ruleta.bala_cerca({1, 2, 3, 4, 5}, huecos=8))


class TestGiroDelTambor(unittest.TestCase):
    def test_la_secuencia_termina_en_el_hueco_elegido(self):
        secuencia = ruleta._secuencia_giro(8, destino=5, vueltas=1)
        self.assertEqual(secuencia[-1], 5)
        self.assertEqual(secuencia[0], 1)
        self.assertEqual(len(secuencia), 13)

    def test_la_secuencia_da_las_vueltas_pedidas(self):
        secuencia = ruleta._secuencia_giro(6, destino=6, vueltas=2)
        self.assertEqual(len(secuencia), 18)
        self.assertEqual(secuencia[-1], 6)

    def test_animar_giro_pinta_hasta_pararse_y_deja_el_tablero_como_estaba(self):
        tablero = ruleta.Tablero(4, {}, [], historial.Historial())
        with patch("ruleta.efectos.repintar") as mock_repintar:
            ruleta.animar_giro(tablero, 3)
        fotogramas = mock_repintar.call_args.args[0]
        self.assertEqual(len(fotogramas), len(ruleta._secuencia_giro(4, 3)))
        self.assertIsNone(tablero.resaltado)

    def test_el_latido_deja_el_tambor_en_reposo(self):
        tablero = ruleta.Tablero(4, {}, [], historial.Historial())
        with patch("ruleta.efectos.repintar") as mock_repintar:
            ruleta.latido(tablero, pulsos=2)
        fotogramas = mock_repintar.call_args.args[0]
        self.assertEqual(len(fotogramas), 4)
        self.assertEqual(fotogramas[-1], ruleta.bloque_tablero(tablero))
        self.assertLess(mock_repintar.call_args.kwargs["factor"], 1)


class TestElegirHueco(unittest.TestCase):
    def _tablero(self):
        return ruleta.Tablero(8, {}, [], historial.Historial())

    def test_sin_teclado_en_crudo_se_teclea_el_numero(self):
        with (
            patch("builtins.input", return_value="4"),
            patch("builtins.print"),
        ):
            elegido = ruleta.elegir_hueco(
                self._tablero(), partial(lambda: None), "Disparar a"
            )
        self.assertEqual(elegido, 4)

    def test_con_teclado_en_crudo_se_usa_el_selector(self):
        tablero = self._tablero()
        with (
            patch("entrada.modo_tecla_disponible", return_value=True),
            patch("entrada.seleccionar", return_value=6) as mock_seleccionar,
        ):
            elegido = ruleta.elegir_hueco(tablero, partial(lambda: None), "Marcar")
        self.assertEqual(elegido, 6)
        mock_seleccionar.assert_called_once()

    def test_el_selector_repinta_la_escena_con_el_hueco_resaltado(self):
        tablero = self._tablero()
        dibujados = []

        def falso_seleccionar(huecos, pintar, inicio=1):
            pintar(3)
            return 3

        with (
            patch("entrada.modo_tecla_disponible", return_value=True),
            patch("entrada.seleccionar", side_effect=falso_seleccionar),
            patch("builtins.print"),
        ):
            ruleta.elegir_hueco(
                tablero,
                partial(lambda: dibujados.append(tablero.resaltado)),
                "Disparar a",
            )

        self.assertEqual(dibujados, [3])
        # El resaltado es cosa del selector: al salir, el tablero vuelve
        # a quedar como estaba para el resto de la interfaz.
        self.assertIsNone(tablero.resaltado)

    def test_cancelar_devuelve_none(self):
        with (
            patch("entrada.modo_tecla_disponible", return_value=True),
            patch("entrada.seleccionar", return_value=None),
        ):
            self.assertIsNone(
                ruleta.elegir_hueco(self._tablero(), partial(lambda: None), "Marcar")
            )


class TestAmbientacion(unittest.TestCase):
    def test_amanecer_anota_el_dia_en_la_bitacora(self):
        bitacora = historial.Historial()
        with patch("builtins.print"):
            ruleta.amanecer(3, bitacora)
        self.assertEqual(bitacora.acciones[-1].tipo, "dia")
        self.assertIn("3", bitacora.acciones[-1].texto)

    def test_el_cartel_de_evento_lleva_su_texto_y_su_pitido(self):
        with (
            patch("ruleta.efectos.banner") as mock_banner,
            patch("ruleta.efectos.beep") as mock_beep,
        ):
            ruleta.cartel_evento("tambor_caliente")
        self.assertIn(
            eventos.texto_de("tambor_caliente"),
            "\n".join(mock_banner.call_args.args[0]),
        )
        mock_beep.assert_called_once_with("zumbido")

    def test_revelar_pista_la_teclea_con_su_numero(self):
        with patch("ruleta.efectos.escribir") as mock_escribir:
            ruleta.revelar_pista(2, pistas.Pista("texto de la pista", frozenset()))
        escrito = mock_escribir.call_args.args[0]
        self.assertIn("#2", escrito)
        self.assertIn("texto de la pista", escrito)


class TestCabecera(unittest.TestCase):
    def test_el_marco_queda_cuadrado(self):
        with patch("builtins.print") as mock_print:
            ruleta.cabecera(4, apuestas.Apuesta(100), farol.Farol(2), num_pistas=3)
        filas = [str(llamada.args[0]) for llamada in mock_print.call_args_list]
        self.assertEqual(
            {efectos.ancho_visible(fila) for fila in filas},
            {ruleta.ANCHO_PANEL + 2},
        )

    def test_el_marco_aguanta_una_apuesta_de_muchas_cifras(self):
        apuesta = apuestas.Apuesta(100)
        for _ in range(20):
            apuesta.doblar()
        with patch("builtins.print") as mock_print:
            ruleta.cabecera(300, apuesta, farol.Farol(2), num_pistas=99)
        filas = [str(llamada.args[0]) for llamada in mock_print.call_args_list]
        self.assertEqual(
            {efectos.ancho_visible(fila) for fila in filas},
            {ruleta.ANCHO_PANEL + 2},
        )

    def test_muestra_dia_puntos_marcas_y_pistas(self):
        with patch("builtins.print") as mock_print:
            ruleta.cabecera(4, apuestas.Apuesta(100), farol.Farol(2), num_pistas=3)
        panel = " ".join(str(llamada.args[0]) for llamada in mock_print.call_args_list)
        self.assertIn("Dia", panel)
        self.assertIn("100", panel)
        self.assertIn("Marcas", panel)
        self.assertIn("Pistas", panel)


class TestPantallasFinales(unittest.TestCase):
    def _mensajes(self, mock_print):
        return " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )

    @patch("ruleta.limpiar", return_value=None)
    def test_impacto_cierra_con_el_epilogo_que_le_pasan(self, mock_limpiar):
        final = ambiente.Epilogo("UN TITULO", "un texto de cierre")
        with patch("builtins.print") as mock_print:
            ruleta.impacto(2, 200, 0, "resumen", final=final)
        mensajes = self._mensajes(mock_print)
        self.assertIn("UN TITULO", mensajes)
        self.assertIn("un texto de cierre", mensajes)

    @patch("ruleta.limpiar", return_value=None)
    def test_impacto_calcula_el_epilogo_si_no_se_lo_dan(self, mock_limpiar):
        with patch("builtins.print") as mock_print:
            ruleta.impacto(2, 200, 0, "resumen")
        self.assertIn("EL NOVATO", self._mensajes(mock_print))

    @patch("ruleta.limpiar", return_value=None)
    def test_retirada_calcula_el_epilogo_si_no_se_lo_dan(self, mock_limpiar):
        with patch("builtins.print") as mock_print:
            ruleta.retirada(3, 400, 1, "resumen")
        self.assertIn("TE RETIRAS A TIEMPO", self._mensajes(mock_print))


class TestFlujoConSelectorCancelado(unittest.TestCase):
    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_echarse_atras_no_gasta_marcas_ni_dispara(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_limpiar,
        mock_pausa,
    ):
        fake = FakeTambor([])
        mock_tambor_cls.side_effect = lambda huecos=None: fake

        entradas = iter(["m", "r", "n"])
        with (
            patch("entrada.modo_tecla_disponible", return_value=True),
            patch("entrada.seleccionar", return_value=None),
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        # Se cancelo el hueco: ni se disparo ni se gasto marca, y el
        # turno volvio a pedir accion (por eso la "r" siguiente cierra).
        self.assertEqual(fake.historial, [])
        _comprobar_final(
            self,
            mock_retirada,
            (0, 100, 0, "Hoy sobreviviste 0 dias, sin faroles ni sobresaltos.", False),
        )


class TestLimpiar(unittest.TestCase):
    def test_delega_en_efectos(self):
        with patch("ruleta.efectos.limpiar") as mock_limpiar:
            ruleta.limpiar(duro=True)
        mock_limpiar.assert_called_once_with(True)


class TestRetiradaConRecord(unittest.TestCase):
    @patch("ruleta.limpiar", return_value=None)
    def test_anuncia_el_nuevo_record(self, mock_limpiar):
        with patch("builtins.print") as mock_print:
            ruleta.retirada(3, 400, 2, "resumen", nuevo_record=True)
        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in mock_print.call_args_list
            if llamada.args
        )
        self.assertIn("Nuevo record", mensajes)


class TestFlujoAvanzado(unittest.TestCase):
    """Ramas del bucle que solo aparecen con las opciones nuevas."""

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_el_modo_oscuridad_apaga_el_tambor_en_cada_turno(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_limpiar,
        mock_pausa,
    ):
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([])

        entradas = iter(["r", "n"])
        with (
            patch("ruleta.oscurecer", return_value={}) as mock_oscurecer,
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar(oscuridad=True)

        mock_oscurecer.assert_called_once()

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_el_tambor_late_cuando_quedan_pocos_huecos(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_limpiar,
        mock_pausa,
    ):
        # Un tambor de 3 huecos ya nace "caliente": no hay margen que
        # gastar antes de que empiece el latido.
        mock_tambor_cls.side_effect = lambda huecos=None: FakeTambor([], huecos=3)

        entradas = iter(["r", "n"])
        with (
            patch("ruleta.latido") as mock_latido,
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar(huecos=3)

        mock_latido.assert_called_once()

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_cancelar_el_disparo_no_gasta_el_turno(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_limpiar,
        mock_pausa,
    ):
        fake = FakeTambor([])
        mock_tambor_cls.side_effect = lambda huecos=None: fake

        entradas = iter(["d", "r", "n"])
        with (
            patch("entrada.modo_tecla_disponible", return_value=True),
            patch("entrada.seleccionar", return_value=None),
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar()

        self.assertEqual(fake.historial, [])

    @patch("ruleta.efectos.pausa", return_value=None)
    @patch("ruleta.limpiar", return_value=None)
    @patch("ruleta.resultado_duelo", return_value=None)
    @patch("ruleta.retirada")
    @patch("ruleta.estado.TamborJuicio")
    @_parchear_records
    def test_en_duelo_tambien_se_puede_cancelar_y_jugar_a_oscuras(
        self,
        mock_cargar,
        mock_guardar,
        mock_tambor_cls,
        mock_retirada,
        mock_resultado,
        mock_limpiar,
        mock_pausa,
    ):
        fake = FakeTambor([], huecos=3)
        mock_tambor_cls.side_effect = lambda huecos=None: fake

        # Nombres, cancelar un farol, cancelar un disparo y retirarse.
        entradas = iter(["Ana", "Bea", "m", "d", "r", "n"])
        with (
            patch("entrada.modo_tecla_disponible", return_value=True),
            patch("entrada.seleccionar", return_value=None),
            patch("ruleta.latido") as mock_latido,
            patch("ruleta.oscurecer", return_value={}) as mock_oscurecer,
            patch("builtins.input", side_effect=lambda _p="": next(entradas)),
            patch("builtins.print"),
        ):
            ruleta.jugar_duelo(huecos=3, oscuridad=True)

        self.assertEqual(fake.historial, [])
        self.assertEqual(mock_oscurecer.call_count, 3)
        self.assertEqual(mock_latido.call_count, 3)
        mock_retirada.assert_called_once()


if __name__ == "__main__":
    unittest.main()
