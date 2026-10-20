extends Control

enum Pantalla { MENU, RECORDS, JUEGO, FIN }

const COLOR_NORMAL := Paleta.NEGRO
const COLOR_BOOM := Color(0.35, 0.03, 0.03, 1)
const COLOR_SUPERVIVENCIA := Color(0.16, 0.13, 0.09, 1)
const COLOR_FAROL_ACIERTO := Color(0.18, 0.15, 0.10, 1)
const COLOR_FAROL_FALLO := Color(0.24, 0.10, 0.10, 1)
const COLOR_RETIRADA := Color(0.14, 0.12, 0.08, 1)

const DURACION_GIRO := 1.1
const DURACION_GIRO_REDUCIDO := 0.35
const DURACION_TENSION := 0.35

const PAUSA_FIN_PARTIDA := 2.0
const DURACION_CIERRE := 0.6

const TAMANO_TEXTO := 16
const AUMENTO_TEXTO := 4

const MEZCLA_CONTRASTE := 0.55

const BUS_MUSICA := "Musica"
const BUS_EFECTOS := "Efectos"

const VOLUMEN_MUSICA_MENU := -20.0
const VOLUMEN_MUSICA_PARTIDA := -13.0
const VOLUMEN_SILENCIO := -80.0

const HUECOS_PARA_TENSION := 3
const ACELERACION_MAXIMA := 0.10

const MAX_BITACORA := 5

@onready var fondo: ColorRect = $Fondo
@onready var fondo_taller: FondoTaller = $FondoTaller
@onready var vineta: Vineta = $Vineta
@onready var centro: CenterContainer = $Centro

@onready var titulo: Label = $Centro/Marco/Columnas/Titulo
@onready var subtitulo: Label = $Centro/Marco/Columnas/Subtitulo

@onready var menu: VBoxContainer = $Centro/Marco/Columnas/Menu
@onready var dificultad_opt: OptionButton = $Centro/Marco/Columnas/Menu/DificultadFila/DificultadOpt
@onready var semilla_campo: LineEdit = $Centro/Marco/Columnas/Menu/SemillaFila/SemillaCampo
@onready var duelo_check: CheckBox = $Centro/Marco/Columnas/Menu/DueloCheck
@onready var nombres_caja: VBoxContainer = $Centro/Marco/Columnas/Menu/Nombres
@onready var nombre1: LineEdit = $Centro/Marco/Columnas/Menu/Nombres/Nombre1
@onready var nombre2: LineEdit = $Centro/Marco/Columnas/Menu/Nombres/Nombre2
@onready var empezar_btn: Button = $Centro/Marco/Columnas/Menu/MenuBotones/EmpezarBtn
@onready var diario_btn: Button = $Centro/Marco/Columnas/Menu/MenuBotones/DiarioBtn
@onready var diario_estado: Label = $Centro/Marco/Columnas/Menu/DiarioEstado
@onready var records_btn: Button = $Centro/Marco/Columnas/Menu/MenuBotones/RecordsBtn

@onready var pantalla_records: VBoxContainer = $Centro/Marco/Columnas/Records
@onready var records_tabla: RichTextLabel = $Centro/Marco/Columnas/Records/Tabla
@onready var etiqueta_records: Label = $Centro/Marco/Columnas/Records/Resumen
@onready var volver_btn: Button = $Centro/Marco/Columnas/Records/VolverBtn

@onready var juego: VBoxContainer = $Centro/Marco/Columnas/Juego
@onready var hud_dia: RichTextLabel = $Centro/Marco/Columnas/Juego/Hud/Fila/Dia/Valor
@onready var hud_puntos: RichTextLabel = $Centro/Marco/Columnas/Juego/Hud/Fila/Puntos/Valor
@onready var hud_pistas: RichTextLabel = $Centro/Marco/Columnas/Juego/Hud/Fila/Pistas/Valor
@onready var hud_marcas: RichTextLabel = $Centro/Marco/Columnas/Juego/Hud/Fila/Marcas/Valor
@onready var etiqueta_turno: Label = $Centro/Marco/Columnas/Juego/Turno
@onready var pistas_scroll: ScrollContainer = $Centro/Marco/Columnas/Juego/PistasScroll
@onready var etiqueta_pistas: Label = $Centro/Marco/Columnas/Juego/PistasScroll/Pistas
@onready var etiqueta_resultado: Label = $Centro/Marco/Columnas/Juego/Resultado
@onready var entrada_numero: LineEdit = $Centro/Marco/Columnas/Juego/EntradaNumero
@onready var disparar_btn: Button = $Centro/Marco/Columnas/Juego/Botones/DispararBtn
@onready var marcar_btn: Button = $Centro/Marco/Columnas/Juego/Botones/MarcarBtn
@onready var retirarse_btn: Button = $Centro/Marco/Columnas/Juego/Botones/RetirarseBtn
@onready var tambor: TamborView = $Centro/Marco/Columnas/Juego/Tambor
@onready var bitacora: RichTextLabel = $Centro/Marco/Columnas/Juego/Bitacora/Lineas

@onready var fin: VBoxContainer = $Centro/Marco/Columnas/Fin
@onready var fin_titulo: Label = $Centro/Marco/Columnas/Fin/Titulo
@onready var fin_resumen: Label = $Centro/Marco/Columnas/Fin/Resumen
@onready var reintentar_btn: Button = $Centro/Marco/Columnas/Fin/Botones/ReintentarBtn
@onready var fin_menu_btn: Button = $Centro/Marco/Columnas/Fin/Botones/MenuBtn

@onready var ayuda: Control = $Ayuda
@onready var ayuda_texto: Label = $Ayuda/Centro/Marco/Columnas/Texto
@onready var pausa: Control = $Pausa
@onready var musica_slider: HSlider = $Pausa/Centro/Marco/Columnas/MusicaFila/MusicaSlider
@onready var efectos_slider: HSlider = $Pausa/Centro/Marco/Columnas/EfectosFila/EfectosSlider
@onready var pantalla_check: CheckBox = $Pausa/Centro/Marco/Columnas/PantallaCheck
@onready var efectos_check: CheckBox = $Pausa/Centro/Marco/Columnas/EfectosCheck
@onready var texto_check: CheckBox = $Pausa/Centro/Marco/Columnas/TextoCheck
@onready var contraste_check: CheckBox = $Pausa/Centro/Marco/Columnas/ContrasteCheck
@onready var sonido_check: CheckBox = $Pausa/Centro/Marco/Columnas/SonidoCheck

@onready var sonido_disparo: AudioStreamPlayer = $SonidoDisparo
@onready var sonido_victoria: AudioStreamPlayer = $SonidoVictoria
@onready var sonido_derrota: AudioStreamPlayer = $SonidoDerrota
@onready var sonido_engranaje: AudioStreamPlayer = $SonidoEngranaje
@onready var sonido_marca: AudioStreamPlayer = $SonidoMarca
@onready var sonido_fallo: AudioStreamPlayer = $SonidoFallo
@onready var sonido_clic: AudioStreamPlayer = $SonidoClic
@onready var sonido_calor: AudioStreamPlayer = $SonidoCalor
@onready var musica_base: AudioStreamPlayer = $MusicaBase
@onready var musica_tension: AudioStreamPlayer = $MusicaTension

var _estado := RuletaEstado.new()
var _records := Records.new()
var _diario := Diario.new()
var _ajustes := Ajustes.new()

var _es_reto_diario := false

var ruta_records := Records.RUTA_POR_DEFECTO
var ruta_ajustes := Ajustes.RUTA_POR_DEFECTO
var ruta_diario := Diario.RUTA_POR_DEFECTO

var _marcadas: Array[int] = []
var _resultados_farol: Dictionary = {}

var _pistas_dudosas: Array[int] = []
var _proxima_pista_dudosa := false

var _lineas_bitacora: Array[String] = []

var _accion_bloqueada := false

var _ultimo_disparo := -1

var _ultima_dificultad := "normal"
var _ultimos_nombres: Array[String] = []

var _colores_originales: Dictionary = {}
var _tamanos_originales: Dictionary = {}
var _colores_tema_originales: Dictionary = {}


func _ready() -> void:
	randomize()
	_encadenar_respaldo_de_fuentes()
	_preparar_buses()

	_estado.partida_iniciada.connect(_on_partida_iniciada)
	_estado.entrada_invalida.connect(_on_entrada_invalida)
	_estado.evento_ocurrido.connect(_on_evento_ocurrido)
	_estado.pista_nueva.connect(_on_pista_nueva)
	_estado.disparo_sobrevivido.connect(_on_disparo_sobrevivido)
	_estado.dia_completado.connect(_on_dia_completado)
	_estado.farol_resuelto.connect(_on_farol_resuelto)
	_estado.impacto.connect(_on_impacto)
	_estado.retirada.connect(_on_retirada)
	_estado.turno_cambiado.connect(_on_turno_cambiado)
	_estado.duelo_terminado.connect(_on_duelo_terminado)

	entrada_numero.text_submitted.connect(func(_texto: String) -> void: _on_disparar_btn_pressed())
	entrada_numero.text_changed.connect(_on_entrada_cambiada)
	duelo_check.toggled.connect(_on_duelo_check_toggled)
	tambor.hueco_pulsado.connect(_on_hueco_pulsado)
	centro.pivot_offset = centro.size / 2.0
	centro.resized.connect(func() -> void: centro.pivot_offset = centro.size / 2.0)

	for clave in Dificultad.ORDEN:
		dificultad_opt.add_item(Dificultad.etiqueta_de(clave))
	dificultad_opt.selected = Dificultad.ORDEN.find("normal")

	_recordar_estilos(self)
	_ajustes = Ajustes.cargar(ruta_ajustes)
	_preparar_controles_de_ajustes()
	_vestir_casillas()
	_arrancar_musica()
	_aplicar_ajustes()

	_records = Records.cargar(ruta_records)
	_diario = Diario.cargar(ruta_diario)
	ayuda.visible = false
	pausa.visible = false
	_mostrar(Pantalla.MENU)


func _encadenar_respaldo_de_fuentes() -> void:
	var respaldo := ThemeDB.fallback_font
	if respaldo == null or theme == null:
		return

	var fuentes: Array[Font] = [theme.default_font]
	if titulo.has_theme_font_override("font"):
		fuentes.append(titulo.get_theme_font("font"))

	for fuente in fuentes:
		if fuente != null and not fuente.fallbacks.has(respaldo):
			fuente.fallbacks = fuente.fallbacks + [respaldo]


func _mostrar(pantalla: Pantalla) -> void:
	menu.visible = pantalla == Pantalla.MENU
	pantalla_records.visible = pantalla == Pantalla.RECORDS
	juego.visible = pantalla == Pantalla.JUEGO
	fin.visible = pantalla == Pantalla.FIN

	titulo.visible = pantalla != Pantalla.JUEGO
	subtitulo.visible = pantalla == Pantalla.MENU

	match pantalla:
		Pantalla.MENU:
			nombres_caja.visible = duelo_check.button_pressed
			fondo.color = COLOR_NORMAL
			diario_estado.text = _diario.resumen()
			empezar_btn.grab_focus()
		Pantalla.RECORDS:
			_pintar_records()
			volver_btn.grab_focus()
		Pantalla.JUEGO:
			entrada_numero.grab_focus()
		Pantalla.FIN:
			reintentar_btn.grab_focus()

	_ajustar_musica()


func _on_diario_btn_pressed() -> void:
	_es_reto_diario = true
	_empezar_partida(Diario.DIFICULTAD, [], Diario.semilla_de_hoy())


func _on_records_btn_pressed() -> void:
	_mostrar(Pantalla.RECORDS)


func _on_volver_btn_pressed() -> void:
	_mostrar(Pantalla.MENU)


func _on_menu_btn_pressed() -> void:
	fondo.color = COLOR_NORMAL
	_mostrar(Pantalla.MENU)


func _on_reintentar_btn_pressed() -> void:
	_es_reto_diario = false
	fondo.color = COLOR_NORMAL
	_empezar_partida(_ultima_dificultad, _ultimos_nombres)


func _pintar_records() -> void:
	etiqueta_records.text = _records.resumen()
	if _records.mejores.is_empty():
		records_tabla.text = "[i]Aun no hay ninguna partida anotada.[/i]"
		return

	var columnas := "%s %s %s  %s" % ["  #", "DIAS".rpad(6), "PUNTOS".rpad(8), "FECHA"]
	var color_cabecera := _con_contraste(Paleta.BRONCE).to_html(false)
	var lineas: Array[String] = ["[color=#%s]%s[/color]" % [color_cabecera, columnas]]
	for i in range(_records.mejores.size()):
		var marca: Dictionary = _records.mejores[i]
		var puesto := ("%d." % (i + 1)).lpad(3)
		var dias := str(marca["dias"]).rpad(6)
		var puntos := str(marca["puntos"]).rpad(8)
		lineas.append("%s %s %s  %s" % [puesto, dias, puntos, marca.get("fecha", "")])
	records_tabla.text = "\n".join(lineas)


func _recordar_estilos(nodo: Node) -> void:
	if nodo is Label or nodo is Button or nodo is RichTextLabel:
		var control := nodo as Control
		if control.has_theme_color_override("font_color"):
			_colores_originales[control] = control.get_theme_color("font_color")
		if control.has_theme_font_size_override("font_size"):
			_tamanos_originales[control] = control.get_theme_font_size("font_size")
		if control.has_theme_font_size_override("normal_font_size"):
			_tamanos_originales[control] = control.get_theme_font_size("normal_font_size")
	for hijo in nodo.get_children():
		_recordar_estilos(hijo)


func _preparar_controles_de_ajustes() -> void:
	efectos_check.button_pressed = _ajustes.efectos_reducidos
	texto_check.button_pressed = _ajustes.texto_grande
	contraste_check.button_pressed = _ajustes.alto_contraste
	sonido_check.button_pressed = _ajustes.sonido
	pantalla_check.button_pressed = _ajustes.pantalla_completa
	musica_slider.value = _ajustes.volumen_musica
	efectos_slider.value = _ajustes.volumen_efectos

	efectos_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("efectos_reducidos", v))
	texto_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("texto_grande", v))
	contraste_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("alto_contraste", v))
	sonido_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("sonido", v))
	pantalla_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("pantalla_completa", v))
	musica_slider.value_changed.connect(
		func(v: float) -> void: _cambiar_ajuste("volumen_musica", v)
	)
	efectos_slider.value_changed.connect(
		func(v: float) -> void: _cambiar_ajuste("volumen_efectos", v)
	)


func _vestir_casillas() -> void:
	var invisible := _icono_invisible()
	for casilla in [
		duelo_check, efectos_check, texto_check, contraste_check, sonido_check, pantalla_check
	]:
		casilla.set_meta("texto_base", casilla.text)
		casilla.add_theme_icon_override("checked", invisible)
		casilla.add_theme_icon_override("unchecked", invisible)
		casilla.add_theme_constant_override("h_separation", 0)
		casilla.toggled.connect(_refrescar_casilla.bind(casilla))
		_refrescar_casilla(casilla.button_pressed, casilla)


func _refrescar_casilla(marcada: bool, casilla: CheckBox) -> void:
	casilla.text = "%s %s" % ["[X]" if marcada else "[ ]", casilla.get_meta("texto_base")]


func _icono_invisible() -> ImageTexture:
	var imagen := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	imagen.fill(Color(0, 0, 0, 0))
	return ImageTexture.create_from_image(imagen)


func _cambiar_ajuste(campo: String, valor: Variant) -> void:
	_ajustes.set(campo, valor)
	_ajustes.guardar(ruta_ajustes)
	_aplicar_ajustes()


func _aplicar_ajustes() -> void:
	fondo_taller.efectos_reducidos = _ajustes.efectos_reducidos
	vineta.efectos_reducidos = _ajustes.efectos_reducidos
	tambor.efectos_reducidos = _ajustes.efectos_reducidos
	tambor.alto_contraste = _ajustes.alto_contraste

	_aplicar_tamano_de_texto()
	_aplicar_contraste()
	_aplicar_volumenes()
	_aplicar_pantalla_completa()

	if not _ajustes.sonido:
		musica_base.stop()
		musica_tension.stop()
	elif not musica_base.playing:
		_arrancar_musica()
	else:
		_ajustar_musica()


func _aplicar_tamano_de_texto() -> void:
	var aumento := AUMENTO_TEXTO if _ajustes.texto_grande else 0
	if theme != null:
		theme.default_font_size = TAMANO_TEXTO + aumento
	for control in _tamanos_originales:
		var original: int = _tamanos_originales[control]
		if control is RichTextLabel:
			control.add_theme_font_size_override("normal_font_size", original + aumento)
		else:
			control.add_theme_font_size_override("font_size", original + aumento)
	for icono in _iconos_del_hud():
		icono.lado = 18.0 + aumento


func _aplicar_contraste() -> void:
	for control in _colores_originales:
		var original: Color = _colores_originales[control]
		control.add_theme_color_override("font_color", _con_contraste(original))
	for icono in _iconos_del_hud():
		icono.color = _con_contraste(Paleta.BRONCE)

	if theme == null:
		return
	for tipo in ["Button", "CheckBox", "OptionButton", "LineEdit"]:
		for nombre in ["font_color", "font_hover_color", "font_pressed_color"]:
			if not theme.has_color(nombre, tipo):
				continue
			var clave := "%s/%s" % [tipo, nombre]
			if not _colores_tema_originales.has(clave):
				_colores_tema_originales[clave] = theme.get_color(nombre, tipo)
			var original: Color = _colores_tema_originales[clave]
			theme.set_color(nombre, tipo, _con_contraste(original))


func _con_contraste(color: Color) -> Color:
	return Paleta.aclarar(color, MEZCLA_CONTRASTE) if _ajustes.alto_contraste else color


func _iconos_del_hud() -> Array[Icono]:
	var iconos: Array[Icono] = []
	for dato in $Centro/Marco/Columnas/Juego/Hud/Fila.get_children():
		var icono := dato.get_node_or_null("Icono") as Icono
		if icono != null:
			iconos.append(icono)
	return iconos


func _aplicar_pantalla_completa() -> void:
	var modo := (
		DisplayServer.WINDOW_MODE_FULLSCREEN
		if _ajustes.pantalla_completa
		else DisplayServer.WINDOW_MODE_WINDOWED
	)
	if DisplayServer.window_get_mode() != modo:
		DisplayServer.window_set_mode(modo)


func _preparar_buses() -> void:
	for nombre in [BUS_MUSICA, BUS_EFECTOS]:
		if AudioServer.get_bus_index(nombre) != -1:
			continue
		AudioServer.add_bus()
		var indice := AudioServer.bus_count - 1
		AudioServer.set_bus_name(indice, nombre)
		AudioServer.set_bus_send(indice, "Master")

	for reproductor in [musica_base, musica_tension]:
		reproductor.bus = BUS_MUSICA
	for reproductor in [
		sonido_disparo,
		sonido_victoria,
		sonido_derrota,
		sonido_engranaje,
		sonido_marca,
		sonido_fallo,
		sonido_clic,
		sonido_calor,
	]:
		reproductor.bus = BUS_EFECTOS


func _aplicar_volumenes() -> void:
	var mezclas := {
		BUS_MUSICA: _ajustes.volumen_musica,
		BUS_EFECTOS: _ajustes.volumen_efectos,
	}
	for nombre in mezclas:
		var indice := AudioServer.get_bus_index(nombre)
		if indice == -1:
			continue
		var valor: float = mezclas[nombre]
		AudioServer.set_bus_mute(indice, valor <= 0.001)
		AudioServer.set_bus_volume_db(indice, linear_to_db(maxf(valor, 0.001)))


func _sonar(reproductor: AudioStreamPlayer) -> void:
	if _ajustes.sonido:
		reproductor.play()


func _arrancar_musica() -> void:
	if not _ajustes.sonido or DisplayServer.get_name() == "headless":
		return
	for reproductor in [musica_base, musica_tension]:
		_poner_en_bucle(reproductor)
		reproductor.volume_db = VOLUMEN_SILENCIO
		reproductor.play()
	_ajustar_musica(2.0)


func _poner_en_bucle(reproductor: AudioStreamPlayer) -> void:
	var flujo := reproductor.stream as AudioStreamWAV
	if flujo == null or flujo.loop_mode == AudioStreamWAV.LOOP_FORWARD:
		return
	flujo.loop_mode = AudioStreamWAV.LOOP_FORWARD
	flujo.loop_begin = 0
	flujo.loop_end = int(flujo.get_length() * flujo.mix_rate)


func _ajustar_musica(duracion: float = 1.0) -> void:
	if not musica_base.playing:
		return

	var en_partida := juego.visible
	var libres := _huecos_libres()
	var total := _estado.tambor.huecos if _estado.tambor != null else RuletaEstado.HUECOS
	var apretado := 1.0 - float(libres) / float(maxi(total, 1))

	var destino_base := VOLUMEN_MUSICA_PARTIDA if en_partida else VOLUMEN_MUSICA_MENU
	var hay_tension := en_partida and libres <= HUECOS_PARA_TENSION
	var destino_tension := VOLUMEN_MUSICA_PARTIDA - 4.0 if hay_tension else VOLUMEN_SILENCIO
	var ritmo := 1.0 + ACELERACION_MAXIMA * apretado if en_partida else 1.0

	var tween := create_tween().set_parallel(true)
	tween.tween_property(musica_base, "volume_db", destino_base, duracion)
	tween.tween_property(musica_tension, "volume_db", destino_tension, duracion)
	for reproductor in [musica_base, musica_tension]:
		tween.tween_property(reproductor, "pitch_scale", ritmo, duracion)


func _huecos_libres() -> int:
	if _estado.tambor == null:
		return RuletaEstado.HUECOS
	return maxi(0, _estado.tambor.huecos - _marcadas.size())


func _exit_tree() -> void:
	for reproductor in [musica_base, musica_tension]:
		reproductor.stop()
		reproductor.stream = null


func _unhandled_input(evento: InputEvent) -> void:
	if not (evento is InputEventKey) or not evento.is_pressed() or evento.is_echo():
		return
	var tecla := evento as InputEventKey
	match tecla.keycode:
		KEY_H:
			_alternar_ayuda()
			get_viewport().set_input_as_handled()
		KEY_ESCAPE:
			if ayuda.visible:
				_alternar_ayuda()
			else:
				_alternar_pausa()
			get_viewport().set_input_as_handled()


func _alternar_ayuda() -> void:
	ayuda.visible = not ayuda.visible
	if not ayuda.visible:
		return
	if pausa.visible:
		_alternar_pausa()
	Maquina.escribir(ayuda_texto, _texto_de_ayuda(), 0, _velocidad_tecleo())
	$Ayuda/Centro/Marco/Columnas/CerrarBtn.grab_focus()


func _on_cerrar_ayuda_pressed() -> void:
	ayuda.visible = false


func _alternar_pausa() -> void:
	pausa.visible = not pausa.visible
	fondo_taller.set_process(pausa.visible == false and not _ajustes.efectos_reducidos)
	if pausa.visible:
		musica_slider.grab_focus()


func _on_cerrar_pausa_pressed() -> void:
	pausa.visible = false
	fondo_taller.set_process(not _ajustes.efectos_reducidos)


func _texto_de_ayuda() -> String:
	return (
		"""El tambor tiene una bala. Cada disparo que falla la mueve un
paso segun un patron oculto: deducirlo es el juego.

DISPARAR arriesga la vida y dobla lo que llevas en juego.
MARCAR gasta una marca para declarar un hueco seguro: si
aciertas ganas %d puntos y si fallas solo pierdes la marca.
RETIRARSE cobra lo acumulado y termina la partida.

Cada %d disparos sobrevividos son un dia de vida, que es lo
que de verdad cuenta para el record.

Elige hueco con el raton o escribiendo su numero. H abre esta
ayuda, Escape abre los ajustes."""
		% [RuletaEstado.BONO_MARCA_ACERTADA, RuletaEstado.DISPAROS_POR_DIA]
	)


func _on_duelo_check_toggled(activado: bool) -> void:
	nombres_caja.visible = activado


func _nombre_de(campo: LineEdit, numero: int) -> String:
	var escrito := campo.text.strip_edges()
	return escrito if escrito != "" else "Jugador %d" % numero


func _on_empezar_btn_pressed() -> void:
	_es_reto_diario = false
	var nombres: Array[String] = []
	if duelo_check.button_pressed:
		nombres = [_nombre_de(nombre1, 1), _nombre_de(nombre2, 2)]
	_empezar_partida(
		Dificultad.ORDEN[dificultad_opt.selected], nombres, Azar.parsear(semilla_campo.text)
	)


func _empezar_partida(dificultad: String, nombres: Array[String], semilla: int = -1) -> void:
	_ultima_dificultad = dificultad
	_ultimos_nombres = nombres.duplicate()
	_mostrar(Pantalla.JUEGO)
	vineta.abrir(DURACION_CIERRE)
	_estado.iniciar_juego(
		Dificultad.huecos_de(dificultad), Dificultad.marcas_de(dificultad), nombres, semilla
	)


func _numero_elegido() -> int:
	return entrada_numero.text.to_int()


func _on_hueco_pulsado(numero: int) -> void:
	if _accion_bloqueada:
		return
	entrada_numero.text = str(numero)
	tambor.elegir(numero)
	_sonar(sonido_clic)


func _on_entrada_cambiada(texto: String) -> void:
	var numero := texto.to_int()
	tambor.elegir(numero if numero >= 1 and numero <= _estado.tambor.huecos else -1)


func _on_disparar_btn_pressed() -> void:
	if _accion_bloqueada:
		return

	var numero := _numero_elegido()
	if numero < 1 or numero > _estado.tambor.huecos:
		_estado.disparar(numero)
		return

	_bloquear_acciones(true)
	_mostrar_resultado("...")

	tambor.acercar()
	_sonar(sonido_engranaje)
	var duracion := DURACION_GIRO_REDUCIDO if _ajustes.efectos_reducidos else DURACION_GIRO
	await tambor.girar(duracion)
	_sonar(sonido_fallo)
	await tambor.tension(numero, DURACION_TENSION)

	_ultimo_disparo = numero
	_mostrar_resultado("")
	_estado.disparar(numero)
	tambor.alejar()


func _on_marcar_btn_pressed() -> void:
	if _accion_bloqueada or not _estado.farol.puede_marcar():
		return

	var numero := _numero_elegido()
	if numero < 1 or numero > _estado.tambor.huecos:
		_estado.marcar(numero)
		return

	_bloquear_acciones(true)
	_mostrar_resultado("...")
	await tambor.tension(numero, DURACION_TENSION)

	_estado.marcar(numero)
	_bloquear_acciones(false)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_retirarse_btn_pressed() -> void:
	if _accion_bloqueada:
		return
	_bloquear_acciones(true)
	_estado.retirarse()


func _on_partida_iniciada(huecos: int, es_duelo: bool) -> void:
	_marcadas.clear()
	_resultados_farol.clear()
	_pistas_dudosas.clear()
	_lineas_bitacora.clear()
	_proxima_pista_dudosa = false
	_ultimo_disparo = -1

	_mostrar_resultado("El tambor esta cargado. Elige una posicion y actua.")
	tambor.preparar_partida(huecos)
	_sonar(sonido_engranaje)
	tambor.girar(DURACION_GIRO)

	entrada_numero.clear()
	entrada_numero.placeholder_text = "Posicion del 1 al %d" % huecos
	entrada_numero.tooltip_text = entrada_numero.placeholder_text
	entrada_numero.grab_focus()

	etiqueta_turno.visible = es_duelo
	if es_duelo:
		var rival := _estado.jugadores[1]
		_refrescar_turno(_estado.jugador_activo.nombre, rival.nombre, rival.dias)

	_bloquear_acciones(false)
	_actualizar_hud()
	_refrescar_pistas()
	_pintar_bitacora()
	fondo.color = COLOR_NORMAL


func _on_entrada_invalida(_numero: int) -> void:
	_mostrar_resultado(
		"Ese numero no esta en el tambor. Elige entre 1 y %d." % _estado.tambor.huecos
	)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_evento_ocurrido(tipo: String, texto: String) -> void:
	_agregar_linea_resultado(texto)
	match tipo:
		"clic_metalico":
			_sonar(sonido_engranaje)
			tambor.barrido()
			vineta.resplandor(Paleta.BRONCE, 0.9)
			_vibrar_pantalla(0.02, 4, 0.25)
		"tambor_caliente":
			_proxima_pista_dudosa = true
			_sonar(sonido_calor)
			fondo_taller.calentar()
			vineta.resplandor(Paleta.ROJO, 1.6)
	_anotar("evento", texto)


func _on_pista_nueva(texto: String, candidatos: Array) -> void:
	if _proxima_pista_dudosa:
		_pistas_dudosas.append(_estado.pistas_reveladas.size() - 1)
		_proxima_pista_dudosa = false
		tambor.destello(_a_huecos(candidatos))
	_refrescar_pistas()
	_anotar("pista", "Pista: %s" % texto)


func _on_disparo_sobrevivido(_disparos: int, en_juego: int) -> void:
	_marcadas.append(_ultimo_disparo)
	_agregar_linea_resultado("Click. Cartucho vacio. Lo apostado se dobla a %d puntos." % en_juego)
	tambor.aplicar_estados(_calcular_estados())
	tambor.pulsar()
	_sonar(sonido_clic)
	_flash(COLOR_SUPERVIVENCIA)
	_anotar("acierto", "Disparaste al %d, cartucho vacio (%d pts)" % [_ultimo_disparo, en_juego])
	_actualizar_hud()
	_ajustar_musica(0.6)
	_bloquear_acciones(false)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_dia_completado(dia: int) -> void:
	_agregar_linea_resultado("Sobrevives al dia %d." % dia)
	_anotar("dia", "Sobrevives al dia %d" % dia)


func _on_farol_resuelto(hueco: int, acierto: bool, en_juego: int, marcas_restantes: int) -> void:
	if acierto:
		_mostrar_resultado(
			(
				"Farol acertado: el hueco %d estaba vacio. +%d puntos."
				% [hueco, RuletaEstado.BONO_MARCA_ACERTADA]
			)
		)
		_sonar(sonido_marca)
		_flash(COLOR_FAROL_ACIERTO)
		_anotar("acierto", "Farol en el %d: acierto (%d pts)" % [hueco, en_juego])
	else:
		_mostrar_resultado("Farol fallido: ahi estaba la bala. Pierdes la marca.")
		_sonar(sonido_fallo)
		_flash(COLOR_FAROL_FALLO)
		_anotar("fallo", "Farol en el %d: ahi estaba la bala" % hueco)

	_resultados_farol[hueco] = (
		TamborView.EstadoHueco.SEGURO if acierto else TamborView.EstadoHueco.PELIGRO
	)
	tambor.aplicar_estados(_calcular_estados())
	tambor.pulsar()
	_actualizar_hud()
	_actualizar_boton_marcar(marcas_restantes)


func _on_turno_cambiado(nombre: String, rival_nombre: String, rival_dias: int) -> void:
	_refrescar_turno(nombre, rival_nombre, rival_dias)
	_actualizar_hud()


func _on_impacto(disparos: int, perdidos: int, dias: int, resumen: String) -> void:
	var nuevo_record := _registrar_en_records(dias, 0)
	_mostrar_resultado(
		(
			"BOOM. %sCaiste tras %d disparo(s) (%d dia(s) sobrevivido(s)), perdiendo %d puntos."
			% [
				_prefijo_jugador(),
				disparos,
				dias,
				perdidos,
			]
		)
	)
	_anotar("muerte", "%sLa bala estaba en el %d" % [_prefijo_jugador(), _ultimo_disparo])

	if _ultimo_disparo != -1:
		var estados := _calcular_estados()
		estados[_ultimo_disparo] = TamborView.EstadoHueco.PELIGRO
		tambor.aplicar_estados(estados)
		tambor.reventar(_ultimo_disparo)
	_sonar(sonido_disparo)
	_sonar(sonido_derrota)
	_flash(COLOR_BOOM)
	vineta.resplandor(Paleta.ROJO, 1.2)
	_vibrar_pantalla()
	_cerrar_partida("HAS MUERTO", resumen, nuevo_record)


func _on_retirada(disparos: int, ganados: int, dias: int, resumen: String) -> void:
	var nuevo_record := _registrar_en_records(dias, ganados)
	_mostrar_resultado(
		(
			"%sTe retira%s a tiempo. Cobra%s %d puntos tras %d disparo(s) (%d dia(s) sobrevivido(s))."
			% [
				_prefijo_jugador(),
				"" if _estado.es_duelo() else "s",
				"" if _estado.es_duelo() else "s",
				ganados,
				disparos,
				dias
			]
		)
	)
	_anotar("acierto", "%sTe retiras con %d puntos" % [_prefijo_jugador(), ganados])

	_sonar(sonido_victoria)
	_flash(COLOR_RETIRADA)
	_cerrar_partida("TE RETIRAS CON VIDA", resumen, nuevo_record)


func _on_duelo_terminado(jugadores: Array, ganadores: Array) -> void:
	var lineas: Array[String] = [""]
	for jugador in jugadores:
		lineas.append(
			(
				"%s: %d dia(s) sobrevividos, %d puntos."
				% [jugador.nombre, jugador.dias, jugador.puntos_finales]
			)
		)
	if ganadores.size() == 1:
		lineas.append("¡Gana %s!" % ganadores[0].nombre)
	else:
		lineas.append("Empate. El tambor no se decide.")
	fin_resumen.text += "\n".join(lineas)
	_agregar_linea_resultado("\n".join(lineas))


func _registrar_en_records(dias: int, puntos: int) -> bool:
	var nuevo_record := dias > _records.dias_maximos
	var bitacora_partida := _estado.historial
	_records.registrar_partida(
		dias, puntos, bitacora_partida.faroles_usados, bitacora_partida.faroles_acertados
	)
	_records.guardar(ruta_records)
	if _es_reto_diario:
		_diario.registrar(dias, puntos)
		_diario.guardar(ruta_diario)
	return nuevo_record


func _prefijo_jugador() -> String:
	return "%s: " % _estado.jugador_activo.nombre if _estado.es_duelo() else ""


func _cerrar_partida(titulo_final: String, resumen: String, nuevo_record: bool) -> void:
	_bloquear_acciones(true)
	fin_titulo.text = titulo_final
	fin_titulo.add_theme_color_override(
		"font_color", _con_contraste(Paleta.ROJO if titulo_final == "HAS MUERTO" else Paleta.BRONCE)
	)
	fin_resumen.text = resumen
	if nuevo_record:
		fin_resumen.text += "\n\n¡Nuevo record de dias sobrevividos!"
	fin_resumen.text += "\n\nSemilla de esta partida: %d" % _estado.semilla
	_esperar_y_mostrar_final.call_deferred()


func _esperar_y_mostrar_final() -> void:
	await get_tree().create_timer(PAUSA_FIN_PARTIDA - DURACION_CIERRE).timeout
	await vineta.cerrar(DURACION_CIERRE)
	Maquina.completar(etiqueta_resultado)
	tambor.alejar(0.1)
	_mostrar(Pantalla.FIN)
	Maquina.escribir(fin_resumen, fin_resumen.text, 0, _velocidad_tecleo())
	vineta.abrir(DURACION_CIERRE)


func _mostrar_resultado(texto: String) -> void:
	Maquina.escribir(etiqueta_resultado, texto, 0, _velocidad_tecleo())


func _agregar_linea_resultado(linea: String) -> void:
	var anterior := etiqueta_resultado.text
	if anterior == "":
		_mostrar_resultado(linea)
		return
	Maquina.escribir(
		etiqueta_resultado, anterior + "\n" + linea, anterior.length(), _velocidad_tecleo()
	)


func _velocidad_tecleo() -> float:
	return 0.0 if _ajustes.efectos_reducidos else Maquina.CARACTERES_POR_SEGUNDO


func _anotar(tipo: String, texto: String) -> void:
	var colores := {
		"acierto": Paleta.BRONCE_VIVO,
		"fallo": Paleta.OXIDO,
		"muerte": Paleta.ROJO,
		"dia": Paleta.BRONCE,
	}
	var color: Color = colores.get(tipo, Paleta.BRONCE_APAGADO)
	_lineas_bitacora.append("[color=#%s]%s[/color]" % [_con_contraste(color).to_html(false), texto])
	if _lineas_bitacora.size() > MAX_BITACORA:
		_lineas_bitacora = _lineas_bitacora.slice(-MAX_BITACORA)
	_pintar_bitacora()


func _pintar_bitacora() -> void:
	if _lineas_bitacora.is_empty():
		bitacora.text = "[i]La partida acaba de empezar.[/i]"
		return
	bitacora.text = "\n".join(_lineas_bitacora)


func _calcular_estados() -> Dictionary:
	var estados := {}
	for hueco in Pistas.interseccion(_estado.pistas_reveladas):
		estados[hueco] = TamborView.EstadoHueco.CANDIDATO
	for hueco in _marcadas:
		estados[hueco] = TamborView.EstadoHueco.PROBADO
	for hueco in _resultados_farol:
		estados[hueco] = _resultados_farol[hueco]
	return estados


func _a_huecos(candidatos: Array) -> Array[int]:
	var huecos: Array[int] = []
	for candidato in candidatos:
		huecos.append(int(candidato))
	return huecos


func _refrescar_turno(nombre: String, rival_nombre: String, rival_dias: int) -> void:
	etiqueta_turno.text = (
		"Turno de %s   ·   %s: %d dia(s) sobrevividos" % [nombre, rival_nombre, rival_dias]
	)


func _actualizar_hud() -> void:
	var dia := _estado.dias_sobrevividos() + 1
	var disparo_del_dia := _estado.disparos % RuletaEstado.DISPAROS_POR_DIA + 1
	_poner_dato(hud_dia, "%d" % dia, "%d/%d" % [disparo_del_dia, RuletaEstado.DISPAROS_POR_DIA])
	_poner_dato(hud_puntos, "%d" % _estado.apuesta.en_juego, "pts")
	_poner_dato(hud_pistas, "%d" % _estado.pistas_reveladas.size(), "pistas")
	_poner_dato(hud_marcas, "%d" % _estado.farol.marcas_restantes, "marcas")


func _poner_dato(etiqueta: RichTextLabel, valor: String, sufijo: String) -> void:
	etiqueta.text = (
		"[b]%s[/b] [color=#%s]%s[/color]"
		% [valor, _con_contraste(Paleta.BRONCE_APAGADO).to_html(false), sufijo]
	)


func _refrescar_pistas() -> void:
	if _estado.pistas_reveladas.is_empty():
		etiqueta_pistas.text = "La bala descansa en algun hueco. Aun no hay pistas."
		return
	var lineas: Array[String] = []
	for i in range(_estado.pistas_reveladas.size()):
		var marca := " (dudosa)" if _pistas_dudosas.has(i) else ""
		lineas.append("#%d %s%s" % [i + 1, _estado.pistas_reveladas[i].texto, marca])
	etiqueta_pistas.text = "\n".join(lineas)
	_bajar_pistas.call_deferred()


func _bajar_pistas() -> void:
	pistas_scroll.scroll_vertical = int(pistas_scroll.get_v_scroll_bar().max_value)


func _actualizar_boton_marcar(marcas_restantes: int) -> void:
	marcar_btn.text = "Marcar (%d)" % marcas_restantes
	marcar_btn.disabled = _accion_bloqueada or marcas_restantes <= 0


func _bloquear_acciones(bloqueada: bool) -> void:
	_accion_bloqueada = bloqueada
	entrada_numero.editable = not bloqueada
	disparar_btn.disabled = bloqueada
	retirarse_btn.disabled = bloqueada
	_actualizar_boton_marcar(
		_estado.farol.marcas_restantes if not _estado.jugadores.is_empty() else 0
	)


func _flash(color: Color) -> void:
	var entrada := 0.5 if _ajustes.efectos_reducidos else 0.15
	var salida := 0.9 if _ajustes.efectos_reducidos else 0.6
	var tween := create_tween()
	tween.tween_property(fondo, "color", color, entrada)
	tween.tween_property(fondo, "color", COLOR_NORMAL, salida)


func _vibrar_pantalla(intensidad: float = 0.05, sacudidas: int = 6, duracion: float = 0.35) -> void:
	if _ajustes.efectos_reducidos:
		return
	var tramo := duracion / float(sacudidas)
	var tween := create_tween()
	for _i in range(sacudidas):
		tween.tween_property(centro, "rotation", randf_range(-intensidad, intensidad), tramo)
	tween.tween_property(centro, "rotation", 0.0, tramo)
