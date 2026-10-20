extends SceneTree

const ESCENA := preload("res://scenes/MainGame.tscn")

const RUTA_RECORDS_TEST := "user://test_escena_records_tmp.json"
const RUTA_AJUSTES_TEST := "user://test_escena_ajustes_tmp.json"
const RUTA_DIARIO_TEST := "user://test_escena_diario_tmp.json"

var _main
var _fallos: Array[String] = []

var _espera_disparo := 0.0
var _espera_farol := 0.0
var _espera_final := 0.0


func _init() -> void:
	_borrar_archivos_test()

	_main = ESCENA.instantiate()
	_main.ruta_records = RUTA_RECORDS_TEST
	_main.ruta_ajustes = RUTA_AJUSTES_TEST
	_main.ruta_diario = RUTA_DIARIO_TEST
	root.add_child(_main)
	await process_frame

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
	await _simular_reto_diario()

	_borrar_archivos_test()
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
	for ruta in [RUTA_RECORDS_TEST, RUTA_AJUSTES_TEST, RUTA_DIARIO_TEST]:
		if FileAccess.file_exists(ruta):
			DirAccess.remove_absolute(ruta)


func _comprobar_tipografia() -> void:
	var courier: FontFile = load("res://assets/fonts/CourierPrime-Regular.ttf")
	var elite: FontFile = load("res://assets/fonts/SpecialElite-Regular.ttf")
	_afirmar(courier != null, "la fuente de la interfaz (Courier Prime) se importa")
	_afirmar(elite != null, "la fuente del titulo (Special Elite) se importa")
	if courier == null or elite == null:
		return

	_afirmar(_main.theme != null, "la escena raiz tiene tema")
	if _main.theme == null:
		return
	_afirmar(
		_main.theme.default_font == courier,
		"el tema pone Courier Prime como fuente por defecto",
	)
	for nodo in [_main.etiqueta_resultado, _main.disparar_btn, _main.dificultad_opt]:
		_afirmar(
			nodo.get_theme_font("font") == courier,
			"%s hereda la tipografia del tema" % nodo.name,
		)
	_afirmar(
		_main.tambor.get_theme_default_font() == courier,
		"el tambor dibuja sus numeros con la tipografia del tema",
	)
	_afirmar(
		_main.titulo.get_theme_font("font") == elite, "el titulo usa Special Elite, no la del tema"
	)

	for glifo in ["·", "¡", "¿"]:
		_afirmar(courier.has_char(glifo.unicode_at(0)), "Courier Prime tiene el glifo '%s'" % glifo)

	_afirmar(
		courier.fallbacks.has(ThemeDB.fallback_font),
		"la fuente de la interfaz encadena el respaldo del motor",
	)


func _comprobar_chapa_del_tema() -> void:
	if _main.theme == null:
		return
	for tipo in ["Button", "LineEdit", "OptionButton", "PanelContainer"]:
		_afirmar(
			_main.theme.has_stylebox("normal", tipo) or _main.theme.has_stylebox("panel", tipo),
			"el tema viste los controles de tipo %s" % tipo,
		)
	_afirmar(
		(
			_main.disparar_btn.get_theme_stylebox("normal")
			== _main.theme.get_stylebox("normal", "Button")
		),
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

	_main.duelo_check.button_pressed = true
	await process_frame
	_afirmar(_main.nombres_caja.visible, "marcar duelo muestra los campos de nombre")
	_main.duelo_check.button_pressed = false
	await process_frame
	_afirmar(not _main.nombres_caja.visible, "desmarcar duelo vuelve a ocultarlos")

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

	_main.efectos_check.button_pressed = false
	_main.contraste_check.button_pressed = false
	_main.texto_check.button_pressed = false
	_main.musica_slider.value = 0.7
	await process_frame
	_afirmar(
		_main.theme.default_font_size == _main.TAMANO_TEXTO,
		"desmarcarlo devuelve el cuerpo original",
	)


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


func _comprobar_hud_inicial() -> void:
	_afirmar(_main.hud_dia.text.find("1") != -1, "el HUD empieza en el dia 1")
	_afirmar(_main.hud_puntos.text.find("100") != -1, "el HUD muestra la apuesta inicial")
	_afirmar(_main.hud_pistas.text.find("0") != -1, "el HUD empieza sin pistas")
	_afirmar(
		_main.hud_marcas.text.find(str(Dificultad.marcas_de("dificil"))) != -1,
		"el HUD muestra las marcas de la dificultad elegida",
	)


func _forzar_bala_lejos() -> void:
	_main._estado.tambor = TamborJuicio.new(6, "avanza", 6)
	_main._estado.probabilidad_eventos = 0.0
	_afirmar(_main._estado.tambor.posicion_bala == 6, "el tambor forzado empieza en el hueco 6")


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
	_main.entrada_numero.text = "6"
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
	_main.entrada_numero.text = "2"
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
	_afirmar(
		_main.fin_resumen.text.find("Nuevo record") == -1,
		"no se anuncia record si no se ha superado",
	)

	_main._on_menu_btn_pressed()
	await process_frame
	_afirmar(_main.menu.visible, "el boton de volver lleva al menu")


func _comprobar_records_guardados() -> void:
	_afirmar(
		FileAccess.file_exists(RUTA_RECORDS_TEST), "la partida ha escrito el archivo de records"
	)
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


func _simular_duelo_completo() -> void:
	await _empezar_partida("normal", ["Ana", "Beto"])
	_afirmar(_main.etiqueta_turno.visible, "en duelo se ve de quien es el turno")
	_afirmar(_main.etiqueta_turno.text.find("Ana") != -1, "empieza el primer jugador")

	_main._estado.tambor = TamborJuicio.new(8, "avanza", 8)
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

	_main._on_retirarse_btn_pressed()
	await process_frame
	var texto: String = _main.etiqueta_resultado.text
	_afirmar(texto.find("Beto") != -1, "el resultado nombra a quien se retira")

	await create_timer(_espera_final).timeout
	_afirmar(_main.fin.visible, "tras el duelo tambien se abre la pantalla de final")
	var resumen: String = _main.fin_resumen.text
	_afirmar(resumen.find("Ana:") != -1, "el veredicto lista a los dos jugadores")
	_afirmar(resumen.find("Gana Ana") != -1, "gana quien acabo con mas puntos")

	_main._on_menu_btn_pressed()
	await process_frame


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
	_afirmar(not _main._proxima_pista_dudosa, "y la sospecha no se arrastra a la pista siguiente")

	_main._on_retirarse_btn_pressed()
	await create_timer(_espera_final).timeout
	_main._on_menu_btn_pressed()
	await process_frame


func _simular_impacto_y_reintento() -> void:
	await _empezar_partida("normal")
	_main._estado.tambor = TamborJuicio.new(8, "avanza", 3)
	_main._estado.probabilidad_eventos = 0.0

	_main.entrada_numero.text = "3"
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(_espera_disparo).timeout
	_afirmar(_main._accion_bloqueada, "tras un impacto, las acciones quedan bloqueadas")
	_afirmar(_main.etiqueta_resultado.text.find("BOOM") != -1, "la pantalla de impacto grita BOOM")
	_afirmar(_main.bitacora.text.find("La bala estaba en el 3") != -1, "la bitacora lo anota")

	await create_timer(_espera_final).timeout
	_afirmar(_main.fin.visible, "tras morir se abre la pantalla de final")
	_afirmar(_main.fin_titulo.text == "HAS MUERTO", "con el rotulo que toca")

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


func _simular_reto_diario() -> void:
	_main._on_diario_btn_pressed()
	await process_frame
	_afirmar(_main._es_reto_diario, "el boton del reto marca la partida como diaria")
	_afirmar(
		_main._estado.semilla == Diario.semilla_de_hoy(),
		"el reto usa la semilla del dia (%d)" % _main._estado.semilla
	)
	_afirmar(
		_main._estado.tambor.huecos == Dificultad.huecos_de(Diario.DIFICULTAD),
		"el reto se juega en normal aunque el menu diga otra cosa"
	)

	_main._on_retirarse_btn_pressed()
	await create_timer(_espera_final).timeout
	_afirmar(_main._diario.jugado_hoy(), "el reto jugado queda anotado en el diario")
	_afirmar(FileAccess.file_exists(RUTA_DIARIO_TEST), "y el diario se escribe a disco")
	_afirmar(_main._diario.racha() == 1, "un dia jugado es una racha de uno")

	_main._on_menu_btn_pressed()
	await process_frame
	_afirmar(
		_main.diario_estado.text.find(Diario.clave_de_hoy()) != -1,
		"el menu dice de que dia es el reto"
	)
	_afirmar(_main.diario_estado.text.find("sin jugar") == -1, "y ya no dice que esta sin jugar")

	_main._on_diario_btn_pressed()
	await process_frame
	_main._on_reintentar_btn_pressed()
	await process_frame
	_afirmar(not _main._es_reto_diario, "reintentar no se juega como reto del dia")
