extends SceneTree
## Test de integracion headless: carga la escena real (MainGame.tscn) y
## simula partidas completas pulsando los mismos metodos que los botones
## y el raton (_on_empezar_btn_pressed, _on_disparar_btn_pressed,
## _on_marcar_btn_pressed, _on_retirarse_btn_pressed, _on_hueco_pulsado),
## esperando de verdad a que las animaciones (Tween) y las pausas terminen
## entre una accion y la siguiente.
##
## A diferencia de test_logica.gd (que prueba RuletaEstado y sus modulos
## de logica pura de forma aislada, sin nodos), este ejercita tambien el
## cableado de señales de MainGame.gd y el paso entre las cuatro pantallas
## (menu, records, partida y final): la parte que test_logica.gd no toca.
## Uso:
##
##   godot --headless --script res://tests/test_escena.gd --path 2d

const ESCENA := preload("res://scenes/MainGame.tscn")

## Los records y los ajustes se redirigen a archivos aparte (ver
## MainGame.ruta_records y MainGame.ruta_ajustes) para no pisar los del
## jugador que ejecute los tests.
const RUTA_RECORDS_TEST := "user://test_escena_records_tmp.json"
const RUTA_AJUSTES_TEST := "user://test_escena_ajustes_tmp.json"

var _main
var _fallos: Array[String] = []

## Lo que hay que esperar a que termine cada accion, calculado a partir de
## las constantes de MainGame para que no se descuadre si alguna cambia.
var _espera_disparo := 0.0
var _espera_farol := 0.0
var _espera_final := 0.0


func _init() -> void:
	_borrar_archivos_test()

	_main = ESCENA.instantiate()
	# Antes de add_child(), o sea antes de que corra _ready() y cargue.
	_main.ruta_records = RUTA_RECORDS_TEST
	_main.ruta_ajustes = RUTA_AJUSTES_TEST
	root.add_child(_main)
	await process_frame  # deja que corra _ready() y sus @onready

	_espera_disparo = _main.DURACION_GIRO + _main.DURACION_TENSION + 0.4
	_espera_farol = _main.DURACION_TENSION + 0.3
	_espera_final = _main.PAUSA_FIN_PARTIDA + _main.DURACION_CIERRE + 0.4

	_comprobar_tipografia()
	_comprobar_chapa_del_tema()
	await _comprobar_menu_inicial()
	await _comprobar_ajustes()
	await _comprobar_ayuda_y_pausa()

	await _empezar_partida("dificil")
	await _comprobar_dificultad_aplicada()
	_comprobar_hud_inicial()

	_forzar_bala_lejos()
	await _simular_eleccion_con_raton()
	await _simular_marcar_acierto()
	await _simular_marcar_fallo()
	await _simular_disparo_seguro()
	await _simular_retirada_y_pantalla_final()
	await _comprobar_records_guardados()

	await _simular_duelo_completo()
	await _simular_pista_dudosa()
	await _simular_impacto_y_reintento()

	_borrar_archivos_test()
	# Desmontaje: la escena se libera a mano porque este script no es la
	# escena principal y nadie mas lo haria, y despues se le da al servidor
	# de audio un rato de reloj (no basta con un fotograma) para descartar
	# los sonidos que quedaran sonando. Sin las dos cosas, Godot avisa al
	# salir de instancias y recursos sin liberar.
	_main.free()
	await create_timer(0.3).timeout

	if _fallos.is_empty():
		print("OK: la escena responde a menu/records/ajustes/partida/final sin errores.")
		quit(0)
	else:
		print("FALLARON %d comprobacion(es):" % _fallos.size())
		for fallo in _fallos:
			print("  - ", fallo)
		quit(1)


func _afirmar(condicion: bool, descripcion: String) -> void:
	if not condicion:
		_fallos.append(descripcion)


func _borrar_archivos_test() -> void:
	for ruta in [RUTA_RECORDS_TEST, RUTA_AJUSTES_TEST]:
		if FileAccess.file_exists(ruta):
			DirAccess.remove_absolute(ruta)


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
	for nodo in [_main.etiqueta_resultado, _main.disparar_btn, _main.dificultad_opt]:
		_afirmar(
			nodo.get_theme_font("font") == courier,
			"%s hereda la tipografia del tema" % nodo.name,
		)
	# TamborView pinta los numeros con get_theme_default_font().
	_afirmar(
		_main.tambor.get_theme_default_font() == courier,
		"el tambor dibuja sus numeros con la tipografia del tema",
	)
	# El titulo y el rotulo del final son las excepciones deliberadas.
	_afirmar(
		_main.titulo.get_theme_font("font") == elite, "el titulo usa Special Elite, no la del tema"
	)

	# Glifos que la interfaz usa de verdad y que no son ASCII: si la
	# fuente no los tuviera, saldrian como recuadros en pantalla.
	for glifo in ["·", "¡", "¿"]:
		_afirmar(courier.has_char(glifo.unicode_at(0)), "Courier Prime tiene el glifo '%s'" % glifo)

	# Un nombre de jugador es texto libre: lo que la fuente no cubra debe
	# caer en el respaldo del motor (ver MainGame._encadenar_respaldo_de_fuentes).
	_afirmar(
		courier.fallbacks.has(ThemeDB.fallback_font),
		"la fuente de la interfaz encadena el respaldo del motor",
	)


## El aspecto de chapa y laton (botones, campos, panel) vive en el mismo
## Theme que la tipografia, y como ella falla en silencio: sin los
## StyleBox, la interfaz saldria con el gris por defecto del motor y en
## headless no se notaria.
func _comprobar_chapa_del_tema() -> void:
	if _main.theme == null:
		return
	for tipo in ["Button", "LineEdit", "OptionButton", "PanelContainer"]:
		_afirmar(
			_main.theme.has_stylebox("normal", tipo) or _main.theme.has_stylebox("panel", tipo),
			"el tema viste los controles de tipo %s" % tipo,
		)
	_afirmar(
		_main.disparar_btn.get_theme_stylebox("normal")
		== _main.theme.get_stylebox("normal", "Button"),
		"los botones cogen su chapa del tema",
	)


func _comprobar_menu_inicial() -> void:
	_afirmar(_main.menu.visible, "al arrancar se ve el menu")
	_afirmar(_main.subtitulo.visible, "y su subtitulo")
	_afirmar(not _main.juego.visible, "al arrancar no se ve el tablero")
	_afirmar(not _main.fin.visible, "ni la pantalla de final")
	_afirmar(not _main.pantalla_records.visible, "ni la de records")
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

	# La pantalla de records va y vuelve sin tocar el resto.
	_main._on_records_btn_pressed()
	await process_frame
	_afirmar(_main.pantalla_records.visible, "el boton de records abre su pantalla")
	_afirmar(not _main.menu.visible, "y esconde el menu")
	_afirmar(
		_main.records_tabla.text.find("ninguna partida") != -1,
		"sin partidas jugadas la tabla lo dice",
	)
	_main._on_volver_btn_pressed()
	await process_frame
	_afirmar(_main.menu.visible, "y se vuelve al menu")


## Los ajustes viven en el panel que abre Escape. Se comprueba que se
## guardan en disco y que llegan a quien los obedece (fondo, viñeta,
## tambor, buses de audio).
func _comprobar_ajustes() -> void:
	_afirmar(not _main.efectos_check.button_pressed, "los efectos empiezan activados")

	_main.efectos_check.button_pressed = true
	_main.contraste_check.button_pressed = true
	_main.texto_check.button_pressed = true
	_main.musica_slider.value = 0.4
	await process_frame

	_afirmar(_main.fondo_taller.efectos_reducidos, "los efectos reducidos llegan al fondo")
	_afirmar(_main.vineta.efectos_reducidos, "los efectos reducidos llegan a la viñeta")
	_afirmar(_main.tambor.efectos_reducidos, "los efectos reducidos llegan al tambor")
	_afirmar(not _main.fondo_taller.is_processing(), "con efectos reducidos el fondo no se repinta")
	_afirmar(_main.tambor.alto_contraste, "el alto contraste llega al tambor")
	_afirmar(
		_main.theme.default_font_size == _main.TAMANO_TEXTO + _main.AUMENTO_TEXTO,
		"el texto grande sube el cuerpo de la tipografia del tema",
	)

	var bus := AudioServer.get_bus_index(_main.BUS_MUSICA)
	_afirmar(bus != -1, "existe el bus de musica")
	if bus != -1:
		_afirmar(
			absf(AudioServer.get_bus_volume_db(bus) - linear_to_db(0.4)) < 0.01,
			"el deslizador de musica llega al bus",
		)

	var guardados := Ajustes.cargar(RUTA_AJUSTES_TEST)
	_afirmar(guardados.efectos_reducidos, "marcar una casilla la guarda en disco")
	_afirmar(guardados.alto_contraste, "y tambien las demas")
	_afirmar(absf(guardados.volumen_musica - 0.4) < 0.001, "el volumen tambien se guarda")

	# Se dejan como estaban: las animaciones siguen probandose en el resto
	# del test, y el tema es un recurso compartido con el resto del juego.
	_main.efectos_check.button_pressed = false
	_main.contraste_check.button_pressed = false
	_main.texto_check.button_pressed = false
	_main.musica_slider.value = 0.7
	await process_frame
	_afirmar(
		_main.theme.default_font_size == _main.TAMANO_TEXTO,
		"desmarcarlo devuelve el cuerpo original",
	)


## Los dos paneles superpuestos: la ayuda (H) y los ajustes (Escape).
func _comprobar_ayuda_y_pausa() -> void:
	_main._alternar_ayuda()
	await process_frame
	_afirmar(_main.ayuda.visible, "H abre la ayuda")
	_afirmar(_main.ayuda_texto.text.find("DISPARAR") != -1, "la ayuda explica las acciones")
	_main._alternar_ayuda()
	await process_frame
	_afirmar(not _main.ayuda.visible, "y volver a pulsar la cierra")

	_main._alternar_pausa()
	await process_frame
	_afirmar(_main.pausa.visible, "Escape abre los ajustes")
	_main._on_cerrar_pausa_pressed()
	await process_frame
	_afirmar(not _main.pausa.visible, "y el boton de seguir los cierra")


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
	_afirmar(not _main.titulo.visible, "y el rotulo deja sitio al tambor")


func _comprobar_dificultad_aplicada() -> void:
	_afirmar(
		_main._estado.tambor.huecos == Dificultad.huecos_de("dificil"),
		"la dificultad elegida fija los huecos del tambor",
	)
	_afirmar(
		_main._estado.farol.marcas_restantes == Dificultad.marcas_de("dificil"),
		"la dificultad elegida fija las marcas de farol",
	)


## Los cuatro datos de la barra superior salen del estado, no de un texto
## escrito a mano en la escena.
func _comprobar_hud_inicial() -> void:
	_afirmar(_main.hud_dia.text.find("1") != -1, "el HUD empieza en el dia 1")
	_afirmar(_main.hud_puntos.text.find("100") != -1, "el HUD muestra la apuesta inicial")
	_afirmar(_main.hud_pistas.text.find("0") != -1, "el HUD empieza sin pistas")
	_afirmar(
		_main.hud_marcas.text.find(str(Dificultad.marcas_de("dificil"))) != -1,
		"el HUD muestra las marcas de la dificultad elegida",
	)


## Sustituye el tambor sorteado por uno determinista (bala en el hueco 6,
## lejos de los 1-3 que vamos a usar) para poder simular sin depender del
## azar. Tambien apaga los eventos, que podrian mover la bala de mas.
func _forzar_bala_lejos() -> void:
	_main._estado.tambor = TamborJuicio.new(6, "avanza", 6)
	_main._estado.probabilidad_eventos = 0.0
	_afirmar(_main._estado.tambor.posicion_bala == 6, "el tambor forzado empieza en el hueco 6")


## Pinchar un hueco del tambor es otra forma de escribir su numero.
func _simular_eleccion_con_raton() -> void:
	_main._on_hueco_pulsado(4)
	await process_frame
	_afirmar(_main.entrada_numero.text == "4", "pinchar un hueco lo escribe en el campo")
	_main.entrada_numero.text = ""
	await process_frame


func _simular_marcar_acierto() -> void:
	_main.entrada_numero.text = "1"
	_main._on_marcar_btn_pressed()
	await process_frame
	await create_timer(_espera_farol).timeout
	_afirmar(_main._estado.farol.marcas_restantes == 1, "marcar acertado consume una marca")
	_afirmar(_main._estado.apuesta.en_juego == 150, "marcar acertado suma el bono (100 -> 150)")
	_afirmar(
		_main._resultados_farol.get(1) == TamborView.EstadoHueco.SEGURO,
		"el hueco marcado y acertado queda en verde",
	)
	_afirmar(_main.hud_puntos.text.find("150") != -1, "y el HUD lo refleja")


func _simular_marcar_fallo() -> void:
	_main.entrada_numero.text = "6"  # ahi esta la bala de verdad
	_main._on_marcar_btn_pressed()
	await process_frame
	await create_timer(_espera_farol).timeout
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
	await create_timer(_espera_disparo).timeout
	_afirmar(_main._estado.disparos == 1, "el disparo fallido cuenta como disparo sobrevivido")
	_afirmar(
		_main._estado.apuesta.en_juego == 300, "un disparo sobrevivido dobla lo que hay en juego"
	)
	_afirmar(_main._marcadas.has(2), "el hueco disparado queda registrado como probado")
	_afirmar(not _main._accion_bloqueada, "tras resolver el disparo, las acciones se desbloquean")
	_afirmar(
		_main.bitacora.text.find("Disparaste al 2") != -1,
		"la bitacora anota el disparo",
	)
	_afirmar(_main.hud_pistas.text.find("1") != -1, "el HUD cuenta la pista nueva")


func _simular_retirada_y_pantalla_final() -> void:
	_main._on_retirarse_btn_pressed()
	await process_frame
	_afirmar(_main._accion_bloqueada, "retirarse bloquea la interfaz")
	_afirmar(
		_main.etiqueta_resultado.text.find("300") != -1,
		"la pantalla de retirada dice cuanto se cobra",
	)

	await create_timer(_espera_final).timeout
	_afirmar(_main.fin.visible, "tras la pausa se abre la pantalla de final")
	_afirmar(not _main.juego.visible, "y el tablero se oculta")
	_afirmar(_main.fin_titulo.text.find("RETIRAS") != -1, "el rotulo dice que salio con vida")
	_afirmar(_main.fin_resumen.text != "", "y hay un resumen de la partida")
	# 0 dias sobrevividos y 0 de record previo: no hay record que batir.
	_afirmar(
		_main.fin_resumen.text.find("Nuevo record") == -1,
		"no se anuncia record si no se ha superado",
	)

	_main._on_menu_btn_pressed()
	await process_frame
	_afirmar(_main.menu.visible, "el boton de volver lleva al menu")


func _comprobar_records_guardados() -> void:
	_afirmar(FileAccess.file_exists(RUTA_RECORDS_TEST), "la partida ha escrito el archivo de records")
	var guardados := Records.cargar(RUTA_RECORDS_TEST)
	_afirmar(guardados.partidas_jugadas == 1, "el archivo cuenta una partida jugada")
	_afirmar(guardados.puntos_maximos == 300, "el archivo guarda los puntos de esa partida")
	_afirmar(guardados.faroles_usados == 2, "el archivo acumula los faroles usados")
	_afirmar(guardados.faroles_acertados == 1, "el archivo acumula los faroles acertados")
	_afirmar(guardados.mejores.size() == 1, "y la partida entra en la tabla de mejores marcas")

	_main._on_records_btn_pressed()
	await process_frame
	_afirmar(
		_main.records_tabla.text.find("300") != -1,
		"la tabla de records muestra la partida recien jugada",
	)
	_afirmar(
		_main.etiqueta_records.text.find("300 puntos") != -1,
		"y el resumen de debajo tambien",
	)
	_main._on_volver_btn_pressed()
	await process_frame


## Duelo entero por la UI: turnos alternos y veredicto en la pantalla final.
func _simular_duelo_completo() -> void:
	await _empezar_partida("normal", ["Ana", "Beto"])
	_afirmar(_main.etiqueta_turno.visible, "en duelo se ve de quien es el turno")
	_afirmar(_main.etiqueta_turno.text.find("Ana") != -1, "empieza el primer jugador")

	_main._estado.tambor = TamborJuicio.new(8, "avanza", 8)  # la bala nunca esta en 1..7
	_main._estado.probabilidad_eventos = 0.0

	_main.entrada_numero.text = "1"
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(_espera_disparo).timeout
	_afirmar(
		_main.etiqueta_turno.text.find("Turno de Beto") != -1,
		"tras el disparo de Ana el turno pasa a Beto",
	)
	_afirmar(
		_main.hud_puntos.text.find("100") != -1,
		"el HUD pasa a mostrar la apuesta de Beto, no la de Ana",
	)

	# Beto se retira: el duelo acaba y se muestra el veredicto.
	_main._on_retirarse_btn_pressed()
	await process_frame
	var texto: String = _main.etiqueta_resultado.text
	_afirmar(texto.find("Beto") != -1, "el resultado nombra a quien se retira")

	await create_timer(_espera_final).timeout
	_afirmar(_main.fin.visible, "tras el duelo tambien se abre la pantalla de final")
	var resumen: String = _main.fin_resumen.text
	_afirmar(resumen.find("Ana:") != -1, "el veredicto lista a los dos jugadores")
	# Ana sobrevivio un disparo (200 en juego), Beto se retiro sin
	# disparar (100): ambos con 0 dias, gana Ana por puntos.
	_afirmar(resumen.find("Gana Ana") != -1, "gana quien acabo con mas puntos")

	_main._on_menu_btn_pressed()
	await process_frame


## Tras un "tambor_caliente", la pista siguiente queda marcada como dudosa
## en la lista. Las dos señales se emiten a mano porque el evento sale por
## sorteo (ver Eventos.tirar_evento) y esperar a que toque haria el test
## dependiente del azar; lo que se prueba aqui es el cableado de la vista,
## no el sorteo, que ya cubre test_logica.gd.
func _simular_pista_dudosa() -> void:
	await _empezar_partida("normal")
	_main._estado.tambor = TamborJuicio.new(8, "avanza", 8)
	_main._estado.probabilidad_eventos = 0.0

	_main.entrada_numero.text = "1"
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(_espera_disparo).timeout
	_afirmar(
		_main.etiqueta_pistas.text.find("(dudosa)") == -1,
		"una pista normal no se marca como dudosa",
	)

	_main._on_evento_ocurrido("tambor_caliente", Eventos.texto_de("tambor_caliente"))
	_afirmar(_main._proxima_pista_dudosa, "el tambor caliente deja la proxima pista bajo sospecha")
	_main._on_pista_nueva("La bala esta en un hueco par.", [2, 4, 6, 8])
	_afirmar(
		_main.etiqueta_pistas.text.find("(dudosa)") != -1,
		"la pista que llega despues sale marcada como dudosa",
	)
	_afirmar(
		not _main._proxima_pista_dudosa, "y la sospecha no se arrastra a la pista siguiente"
	)

	_main._on_retirarse_btn_pressed()
	await create_timer(_espera_final).timeout
	_main._on_menu_btn_pressed()
	await process_frame


func _simular_impacto_y_reintento() -> void:
	await _empezar_partida("normal")
	_main._estado.tambor = TamborJuicio.new(8, "avanza", 3)
	_main._estado.probabilidad_eventos = 0.0

	_main.entrada_numero.text = "3"  # justo la bala
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(_espera_disparo).timeout
	_afirmar(_main._accion_bloqueada, "tras un impacto, las acciones quedan bloqueadas")
	_afirmar(
		_main.etiqueta_resultado.text.find("BOOM") != -1, "la pantalla de impacto grita BOOM"
	)
	_afirmar(_main.bitacora.text.find("La bala estaba en el 3") != -1, "la bitacora lo anota")

	await create_timer(_espera_final).timeout
	_afirmar(_main.fin.visible, "tras morir se abre la pantalla de final")
	_afirmar(_main.fin_titulo.text == "HAS MUERTO", "con el rotulo que toca")

	# Reintentar repite la misma configuracion sin pasar por el menu.
	_main._on_reintentar_btn_pressed()
	await process_frame
	_afirmar(_main.juego.visible, "reintentar vuelve directo a la partida")
	_afirmar(
		_main._estado.tambor.huecos == Dificultad.huecos_de("normal"),
		"y repite la dificultad de la partida anterior",
	)
	_afirmar(_main._estado.disparos == 0, "con el tambor reseteado")

	_main._on_retirarse_btn_pressed()
	await create_timer(_espera_final).timeout
	_main._on_menu_btn_pressed()
	await process_frame
