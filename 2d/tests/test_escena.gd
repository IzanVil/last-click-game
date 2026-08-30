extends SceneTree
## Test de integracion headless: carga la escena real (MainGame.tscn) y
## simula partidas completas pulsando los mismos metodos que los botones
## (_on_empezar_btn_pressed, _on_disparar_btn_pressed,
## _on_marcar_btn_pressed, _on_retirarse_btn_pressed), esperando de
## verdad a que las animaciones (Tween) y las pausas terminen entre una
## accion y la siguiente.
##
## A diferencia de test_logica.gd (que prueba RuletaEstado y sus modulos
## de logica pura de forma aislada, sin nodos), este ejercita tambien el
## cableado de señales de MainGame.gd: la parte que test_logica.gd no
## toca. Uso:
##
##   godot --headless --script res://tests/test_escena.gd --path 2d

const ESCENA := preload("res://scenes/MainGame.tscn")

## Los records se redirigen a un archivo aparte (ver MainGame.ruta_records)
## para no pisar los del jugador que ejecute los tests.
const RUTA_RECORDS_TEST := "user://test_escena_records_tmp.json"

var _main
var _fallos: Array[String] = []


func _init() -> void:
	_borrar_records_test()

	_main = ESCENA.instantiate()
	# Antes de add_child(), o sea antes de que corra _ready() y cargue.
	_main.ruta_records = RUTA_RECORDS_TEST
	root.add_child(_main)
	await process_frame  # deja que corra _ready() y sus @onready

	_comprobar_tipografia()
	await _comprobar_menu_inicial()
	await _empezar_partida("dificil")
	await _comprobar_dificultad_aplicada()

	_forzar_bala_lejos()
	await _simular_marcar_acierto()
	await _simular_marcar_fallo()
	await _simular_disparo_seguro()
	await _simular_retirada_y_vuelta_al_menu()
	_comprobar_records_guardados()

	await _simular_duelo_completo()
	await _simular_impacto()

	_borrar_records_test()

	if _fallos.is_empty():
		print("OK: la escena responde a menu/disparar/marcar/retirarse/duelo sin errores.")
		quit(0)
	else:
		print("FALLARON %d comprobacion(es):" % _fallos.size())
		for fallo in _fallos:
			print("  - ", fallo)
		quit(1)


func _afirmar(condicion: bool, descripcion: String) -> void:
	if not condicion:
		_fallos.append(descripcion)


func _borrar_records_test() -> void:
	if FileAccess.file_exists(RUTA_RECORDS_TEST):
		DirAccess.remove_absolute(RUTA_RECORDS_TEST)


## La tipografia de maquina de escribir se aplica via Theme, y un fallo
## ahi (un .tres mal referenciado, un .ttf que no importa) no da error:
## la interfaz simplemente saldria con la fuente por defecto de Godot y
## en headless no se notaria. De ahi que se compruebe explicitamente.
func _comprobar_tipografia() -> void:
	var courier: FontFile = load("res://assets/fonts/CourierPrime-Regular.ttf")
	var elite: FontFile = load("res://assets/fonts/SpecialElite-Regular.ttf")
	_afirmar(courier != null, "la fuente de la interfaz (Courier Prime) se importa")
	_afirmar(elite != null, "la fuente del titulo (Special Elite) se importa")
	if courier == null or elite == null:
		return

	_afirmar(_main.theme != null, "la escena raiz tiene tema")
	if _main.theme == null:
		return  # sin tema, las comprobaciones de abajo no tienen sentido
	_afirmar(
		_main.theme.default_font == courier,
		"el tema pone Courier Prime como fuente por defecto",
	)
	# Los nodos la heredan del tema, sin override nodo por nodo.
	for nodo in [_main.etiqueta_cabecera, _main.disparar_btn, _main.dificultad_opt]:
		_afirmar(
			nodo.get_theme_font("font") == courier,
			"%s hereda la tipografia del tema" % nodo.name,
		)
	# TamborView pinta los numeros con get_theme_default_font().
	_afirmar(
		_main.tambor.get_theme_default_font() == courier,
		"el tambor dibuja sus numeros con la tipografia del tema",
	)
	# El titulo es la excepcion deliberada.
	var titulo: Label = _main.get_node("Centro/Columnas/Titulo")
	_afirmar(
		titulo.get_theme_font("font") == elite, "el titulo usa Special Elite, no la del tema"
	)

	# Glifos que la interfaz usa de verdad y que no son ASCII: si la
	# fuente no los tuviera, saldrian como recuadros en pantalla.
	for glifo in ["·", "¡"]:
		_afirmar(courier.has_char(glifo.unicode_at(0)), "Courier Prime tiene el glifo '%s'" % glifo)

	# Un nombre de jugador es texto libre: lo que la fuente no cubra debe
	# caer en el respaldo del motor (ver MainGame._encadenar_respaldo_de_fuentes).
	_afirmar(
		courier.fallbacks.has(ThemeDB.fallback_font),
		"la fuente de la interfaz encadena el respaldo del motor",
	)


func _comprobar_menu_inicial() -> void:
	_afirmar(_main.menu.visible, "al arrancar se ve el menu")
	_afirmar(not _main.juego.visible, "al arrancar no se ve el tablero")
	_afirmar(
		_main.dificultad_opt.item_count == Dificultad.ORDEN.size(),
		"el desplegable ofrece las tres dificultades",
	)
	_afirmar(
		not _main.nombres_caja.visible,
		"los nombres estan ocultos mientras el duelo no este marcado",
	)

	# Marcar el duelo revela los campos de nombre, y desmarcarlo los oculta.
	_main.duelo_check.button_pressed = true
	await process_frame
	_afirmar(_main.nombres_caja.visible, "marcar duelo muestra los campos de nombre")
	_main.duelo_check.button_pressed = false
	await process_frame
	_afirmar(not _main.nombres_caja.visible, "desmarcar duelo vuelve a ocultarlos")


func _empezar_partida(dificultad: String, nombres: Array = []) -> void:
	_main.dificultad_opt.selected = Dificultad.ORDEN.find(dificultad)
	_main.duelo_check.button_pressed = not nombres.is_empty()
	if not nombres.is_empty():
		_main.nombre1.text = nombres[0]
		_main.nombre2.text = nombres[1]
	_main._on_empezar_btn_pressed()
	await process_frame
	_afirmar(not _main.menu.visible, "al empezar se oculta el menu")
	_afirmar(_main.juego.visible, "al empezar se ve el tablero")


func _comprobar_dificultad_aplicada() -> void:
	_afirmar(
		_main._estado.tambor.huecos == Dificultad.huecos_de("dificil"),
		"la dificultad elegida fija los huecos del tambor",
	)
	_afirmar(
		_main._estado.farol.marcas_restantes == Dificultad.marcas_de("dificil"),
		"la dificultad elegida fija las marcas de farol",
	)


## Sustituye el tambor sorteado por uno determinista (bala en el hueco 6,
## lejos de los 1-3 que vamos a usar) para poder simular sin depender del
## azar. Tambien apaga los eventos, que podrian mover la bala de mas.
func _forzar_bala_lejos() -> void:
	_main._estado.tambor = TamborJuicio.new(6, "avanza", 6)
	_main._estado.probabilidad_eventos = 0.0
	_afirmar(_main._estado.tambor.posicion_bala == 6, "el tambor forzado empieza en el hueco 6")


func _simular_marcar_acierto() -> void:
	_main.entrada_numero.text = "1"
	_main._on_marcar_btn_pressed()
	await process_frame
	await create_timer(0.6).timeout  # tension() dura 0.5s
	_afirmar(_main._estado.farol.marcas_restantes == 1, "marcar acertado consume una marca")
	_afirmar(_main._estado.apuesta.en_juego == 150, "marcar acertado suma el bono (100 -> 150)")
	_afirmar(
		_main._resultados_farol.get(1) == TamborView.EstadoHueco.SEGURO,
		"el hueco marcado y acertado queda en verde",
	)


func _simular_marcar_fallo() -> void:
	_main.entrada_numero.text = "6"  # ahi esta la bala de verdad
	_main._on_marcar_btn_pressed()
	await process_frame
	await create_timer(0.6).timeout
	_afirmar(_main._estado.farol.marcas_restantes == 0, "marcar fallido tambien consume la marca")
	_afirmar(_main._estado.apuesta.en_juego == 150, "marcar fallido no toca los puntos")
	_afirmar(
		_main._resultados_farol.get(6) == TamborView.EstadoHueco.PELIGRO,
		"el hueco marcado y fallado queda en rojo",
	)
	_afirmar(_main.marcar_btn.disabled, "sin marcas, el boton de marcar se deshabilita")


func _simular_disparo_seguro() -> void:
	_main.entrada_numero.text = "2"  # falla: la bala sigue en 6
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(0.6).timeout
	_afirmar(_main._estado.disparos == 1, "el disparo fallido cuenta como disparo sobrevivido")
	_afirmar(
		_main._estado.apuesta.en_juego == 300, "un disparo sobrevivido dobla lo que hay en juego"
	)
	_afirmar(_main._marcadas.has(2), "el hueco disparado queda registrado como probado")
	_afirmar(not _main._accion_bloqueada, "tras resolver el disparo, las acciones se desbloquean")


func _simular_retirada_y_vuelta_al_menu() -> void:
	_main._on_retirarse_btn_pressed()
	await process_frame
	_afirmar(_main._accion_bloqueada, "retirarse bloquea la interfaz")
	_afirmar(
		_main.etiqueta_resultado.text.find("300") != -1,
		"la pantalla de retirada dice cuanto se cobra",
	)
	# 0 dias sobrevividos y 0 de record previo: no hay record que batir.
	_afirmar(
		_main.etiqueta_resultado.text.find("Nuevo record") == -1,
		"no se anuncia record si no se ha superado",
	)

	await create_timer(_main.PAUSA_FIN_PARTIDA + 0.6).timeout
	_afirmar(_main.menu.visible, "tras la pausa se vuelve al menu")
	_afirmar(not _main.juego.visible, "y el tablero se oculta")


func _comprobar_records_guardados() -> void:
	_afirmar(FileAccess.file_exists(RUTA_RECORDS_TEST), "la partida ha escrito el archivo de records")
	var guardados := Records.cargar(RUTA_RECORDS_TEST)
	_afirmar(guardados.partidas_jugadas == 1, "el archivo cuenta una partida jugada")
	_afirmar(guardados.puntos_maximos == 300, "el archivo guarda los puntos de esa partida")
	_afirmar(guardados.faroles_usados == 2, "el archivo acumula los faroles usados")
	_afirmar(guardados.faroles_acertados == 1, "el archivo acumula los faroles acertados")
	_afirmar(
		_main.etiqueta_records.text.find("300 puntos") != -1,
		"el menu muestra ya los records actualizados",
	)


## Duelo entero por la UI: turnos alternos y veredicto final en pantalla.
func _simular_duelo_completo() -> void:
	await _empezar_partida("normal", ["Ana", "Beto"])
	_afirmar(_main.etiqueta_turno.visible, "en duelo se ve de quien es el turno")
	_afirmar(_main.etiqueta_turno.text.find("Ana") != -1, "empieza el primer jugador")

	_main._estado.tambor = TamborJuicio.new(8, "avanza", 8)  # la bala nunca esta en 1..7
	_main._estado.probabilidad_eventos = 0.0

	_main.entrada_numero.text = "1"
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(0.6).timeout
	_afirmar(
		_main.etiqueta_turno.text.find("Turno de Beto") != -1,
		"tras el disparo de Ana el turno pasa a Beto",
	)
	_afirmar(
		_main.etiqueta_cabecera.text.find("100 pts") != -1,
		"la cabecera pasa a mostrar la apuesta de Beto, no la de Ana",
	)

	# Beto se retira: el duelo acaba y se muestra el veredicto.
	_main._on_retirarse_btn_pressed()
	await process_frame
	var texto: String = _main.etiqueta_resultado.text
	_afirmar(texto.find("Beto") != -1, "el resultado nombra a quien se retira")
	_afirmar(texto.find("Ana:") != -1, "el veredicto lista tambien al rival")
	# Ana sobrevivio un disparo (200 en juego), Beto se retiro sin
	# disparar (100): ambos con 0 dias, gana Ana por puntos.
	_afirmar(texto.find("Gana Ana") != -1, "gana quien acabo con mas puntos")

	await create_timer(_main.PAUSA_FIN_PARTIDA + 0.6).timeout
	_afirmar(_main.menu.visible, "tras el duelo tambien se vuelve al menu")


func _simular_impacto() -> void:
	await _empezar_partida("normal")
	_main._estado.tambor = TamborJuicio.new(8, "avanza", 3)
	_main._estado.probabilidad_eventos = 0.0

	_main.entrada_numero.text = "3"  # justo la bala
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(1.0).timeout  # tension() (0.5s) + margen hasta _on_impacto
	_afirmar(_main._accion_bloqueada, "tras un impacto, las acciones quedan bloqueadas")
	_afirmar(
		_main.etiqueta_resultado.text.find("BOOM") != -1, "la pantalla de impacto grita BOOM"
	)

	await create_timer(_main.PAUSA_FIN_PARTIDA + 0.6).timeout
	_afirmar(_main.menu.visible, "tras morir tambien se vuelve al menu")

