extends Control
## Vista de "El Tambor del Juicio": escucha las señales de RuletaEstado
## y actualiza Label/Button/Tween/TamborView en pantalla.
##
## No conoce reglas del juego (bala, apuestas, farol, dias... viven en
## RuletaEstado y los modulos que orquesta). Hermano de terminal/ruleta.py:
## misma separacion entre logica pura e interfaz, misma orquestacion de
## disparar/marcar/retirarse, adaptada de teclado+colores ANSI a
## botones+Tween.
##
## Donde la terminal usa argparse (--dificultad, --duelo, --records),
## aqui hay un menu previo a la partida con los mismos ajustes; y donde
## alli se vuelve al prompt al morir, aqui se vuelve a ese menu, con los
## records ya actualizados a la vista.
##
## La ambientacion (engranajes del fondo, viñeta, resplandores, tecleo del
## texto, ambiente sonoro) vive en nodos aparte —FondoTaller, Vineta,
## Maquina, los AudioStreamPlayer— que no saben nada del juego: es este
## script el que decide cuando pedirles algo, igual que decide cuando
## pintar una etiqueta.

const COLOR_NORMAL := Color(0.09, 0.08, 0.07, 1)
const COLOR_BOOM := Color(0.42, 0.05, 0.05, 1)
const COLOR_SUPERVIVENCIA := Color(0.2, 0.16, 0.06, 1)
const COLOR_FAROL_ACIERTO := Color(0.08, 0.22, 0.14, 1)
const COLOR_FAROL_FALLO := Color(0.3, 0.07, 0.07, 1)
const COLOR_RETIRADA := Color(0.12, 0.2, 0.13, 1)
const COLOR_RECORD := Color(0.78, 0.58, 0.16, 1)

## Colores de los resplandores de borde que acompañan a los dos eventos
## (ver Vineta.resplandor y Eventos.gd).
const COLOR_CALOR := Color(0.85, 0.15, 0.06, 1)
const COLOR_CLIC := Color(0.75, 0.66, 0.45, 1)

## Cuanto se queda en pantalla el resultado final antes de volver al menu,
## y cuanto de esa pausa se va en cerrar la pantalla en iris. El cierre va
## dentro de la pausa (no despues) para que el ritmo del fin de partida no
## dependa de si los efectos estan activados.
const PAUSA_FIN_PARTIDA := 2.6
const DURACION_CIERRE := 0.6

## Cuerpo base de la tipografia y cuanto crece con "texto grande".
const TAMANO_TEXTO := 16
const AUMENTO_TEXTO := 4

## Cuanto se acerca al blanco cada color de texto en alto contraste. Se
## mezcla en vez de sustituirse por un blanco plano para no perder el
## codigo de color (laton en los titulos, apagado en lo secundario).
const MEZCLA_CONTRASTE := 0.55

## Volumen del ambiente en el menu y durante la partida: el bordon aprieta
## un poco cuando hay algo en juego.
const VOLUMEN_AMBIENTE_MENU := -26.0
const VOLUMEN_AMBIENTE_PARTIDA := -18.0
const VOLUMEN_AMBIENTE_MUDO := -80.0

## Cuanto se acelera el ambiente mientras el tambor esta caliente.
const PITCH_AMBIENTE_CALIENTE := 1.12

@onready var fondo: ColorRect = $Fondo
@onready var fondo_taller: FondoTaller = $FondoTaller
@onready var vineta: Vineta = $Vineta
@onready var centro: CenterContainer = $Centro

@onready var menu: VBoxContainer = $Centro/Marco/Columnas/Menu
@onready var etiqueta_records: Label = $Centro/Marco/Columnas/Menu/Records
@onready var dificultad_opt: OptionButton = $Centro/Marco/Columnas/Menu/DificultadFila/DificultadOpt
@onready var duelo_check: CheckBox = $Centro/Marco/Columnas/Menu/DueloCheck
@onready var nombres_caja: VBoxContainer = $Centro/Marco/Columnas/Menu/Nombres
@onready var nombre1: LineEdit = $Centro/Marco/Columnas/Menu/Nombres/Nombre1
@onready var nombre2: LineEdit = $Centro/Marco/Columnas/Menu/Nombres/Nombre2
@onready var empezar_btn: Button = $Centro/Marco/Columnas/Menu/EmpezarBtn

@onready var efectos_check: CheckBox = $Centro/Marco/Columnas/Menu/Ajustes/EfectosCheck
@onready var texto_check: CheckBox = $Centro/Marco/Columnas/Menu/Ajustes/TextoCheck
@onready var contraste_check: CheckBox = $Centro/Marco/Columnas/Menu/Ajustes/ContrasteCheck
@onready var sonido_check: CheckBox = $Centro/Marco/Columnas/Menu/Ajustes/SonidoCheck

@onready var juego: VBoxContainer = $Centro/Marco/Columnas/Juego
@onready var etiqueta_turno: Label = $Centro/Marco/Columnas/Juego/Turno
@onready var etiqueta_cabecera: Label = $Centro/Marco/Columnas/Juego/Cabecera
@onready var pistas_scroll: ScrollContainer = $Centro/Marco/Columnas/Juego/PistasScroll
@onready var etiqueta_pistas: Label = $Centro/Marco/Columnas/Juego/PistasScroll/Pistas
@onready var etiqueta_resultado: Label = $Centro/Marco/Columnas/Juego/Resultado
@onready var entrada_numero: LineEdit = $Centro/Marco/Columnas/Juego/EntradaNumero
@onready var disparar_btn: Button = $Centro/Marco/Columnas/Juego/Botones/DispararBtn
@onready var marcar_btn: Button = $Centro/Marco/Columnas/Juego/Botones/MarcarBtn
@onready var retirarse_btn: Button = $Centro/Marco/Columnas/Juego/Botones/RetirarseBtn
@onready var tambor: TamborView = $Centro/Marco/Columnas/Juego/Tambor

@onready var sonido_disparo: AudioStreamPlayer = $SonidoDisparo
@onready var sonido_victoria: AudioStreamPlayer = $SonidoVictoria
@onready var sonido_derrota: AudioStreamPlayer = $SonidoDerrota
@onready var sonido_engranaje: AudioStreamPlayer = $SonidoEngranaje
@onready var sonido_marca: AudioStreamPlayer = $SonidoMarca
@onready var sonido_fallo: AudioStreamPlayer = $SonidoFallo
@onready var sonido_ambiente: AudioStreamPlayer = $SonidoAmbiente

var _estado := RuletaEstado.new()
var _records := Records.new()
var _ajustes := Ajustes.new()

## Archivos donde se leen y guardan records y ajustes. Son variables, y no
## las constantes RUTA_POR_DEFECTO usadas directamente, para que los tests
## puedan redirigirlas (antes de add_child, o sea antes de _ready) y no
## pisar los del jugador que los ejecute. Mismo motivo que
## RuletaEstado.probabilidad_eventos.
var ruta_records := Records.RUTA_POR_DEFECTO
var ruta_ajustes := Ajustes.RUTA_POR_DEFECTO

## Huecos ya disparados (gris) y resultados de farol por hueco (verde o
## rojo, ver TamborView.EstadoHueco). Igual que en terminal/ruleta.py,
## esto no vive en la logica pura: es memoria de la vista. En duelo son
## compartidos, como el propio tambor.
var _marcadas: Array[int] = []
var _resultados_farol: Dictionary = {}

## Indices (dentro de _estado.pistas_reveladas) de las pistas que llegaron
## justo despues de un "tambor_caliente" y por tanto pueden ser mentira.
## El jugador ya lo sabe —el evento se lo dijo por escrito— asi que
## marcarlas en la lista no le regala informacion: solo le ahorra tener
## que acordarse de cual era.
var _pistas_dudosas: Array[int] = []
var _proxima_pista_dudosa := false

## Evita disparos/faroles dobles mientras hay una animacion en marcha o
## la partida ya ha terminado: el resultado esta decidido, pero la
## vista aun no ha terminado de mostrarlo.
var _accion_bloqueada := false

## Numero sobre el que se disparo por ultima vez, para poder marcarlo
## como "probado" (o, si mata, en rojo) cuando llega la señal
## correspondiente: esas señales no llevan el numero porque tambien las
## usa la version de terminal, que no necesita repetirlo (ya lo tiene
## en su propio bucle).
var _ultimo_disparo := -1

## Colores y cuerpos de letra tal como venian de la escena, para poder
## volver a ellos al desmarcar "alto contraste" o "texto grande" (ver
## _recordar_estilos).
var _colores_originales: Dictionary = {}
var _tamanos_originales: Dictionary = {}
var _colores_tema_originales: Dictionary = {}


func _ready() -> void:
	randomize()
	_encadenar_respaldo_de_fuentes()
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
	duelo_check.toggled.connect(_on_duelo_check_toggled)
	centro.pivot_offset = centro.size / 2.0
	centro.resized.connect(func() -> void: centro.pivot_offset = centro.size / 2.0)

	for clave in Dificultad.ORDEN:
		dificultad_opt.add_item(Dificultad.etiqueta_de(clave))
	dificultad_opt.selected = Dificultad.ORDEN.find("normal")

	_recordar_estilos(self)
	_ajustes = Ajustes.cargar(ruta_ajustes)
	_preparar_casillas_de_ajustes()
	_vestir_casillas()
	# El ambiente arranca antes de aplicar los ajustes para que estos solo
	# tengan que ajustarle el volumen, y no decidir tambien si suena.
	_arrancar_ambiente()
	_aplicar_ajustes()

	_records = Records.cargar(ruta_records)
	_mostrar_menu()


## Encadena la fuente por defecto del motor como respaldo de las dos
## tipografias del juego.
##
## Courier Prime y Special Elite solo cubren alfabeto latino, y el nombre
## de un jugador es texto libre: sin respaldo, alguien que escriba su
## nombre en cirilico (o con un emoji) veria un recuadro de sustitucion
## en vez de sus letras. Se hace aqui en codigo, y no en el .tres del
## tema, porque `fallbacks` es una propiedad de la FontFile importada y
## una escena solo puede referenciarla, no añadirle propiedades.
func _encadenar_respaldo_de_fuentes() -> void:
	var respaldo := ThemeDB.fallback_font
	# Si el tema no cargase, la interfaz saldria con la tipografia por
	# defecto del motor: feo, pero jugable. No merece tumbar el juego
	# entero en _ready() por un problema puramente cosmetico.
	if respaldo == null or theme == null:
		return

	var fuentes: Array[Font] = [theme.default_font]
	var titulo := $Centro/Marco/Columnas/Titulo as Label
	if titulo.has_theme_font_override("font"):
		fuentes.append(titulo.get_theme_font("font"))

	for fuente in fuentes:
		if fuente != null and not fuente.fallbacks.has(respaldo):
			fuente.fallbacks = fuente.fallbacks + [respaldo]


# --- Ajustes de accesibilidad -------------------------------------------------


## Guarda el color y el cuerpo de letra que cada nodo trae de la escena,
## recorriendo el arbol una sola vez. Con eso, "alto contraste" y "texto
## grande" pueden aplicarse y deshacerse sin que la escena tenga que
## enumerar sus propias etiquetas en una lista que envejeceria mal.
func _recordar_estilos(nodo: Node) -> void:
	if nodo is Label or nodo is Button:
		var control := nodo as Control
		if control.has_theme_color_override("font_color"):
			_colores_originales[control] = control.get_theme_color("font_color")
		if control.has_theme_font_size_override("font_size"):
			_tamanos_originales[control] = control.get_theme_font_size("font_size")
	for hijo in nodo.get_children():
		_recordar_estilos(hijo)


func _preparar_casillas_de_ajustes() -> void:
	# Primero el valor cargado y despues la conexion: al reves, marcar las
	# casillas al arrancar dispararia el guardado de lo que se acaba de leer.
	efectos_check.button_pressed = _ajustes.efectos_reducidos
	texto_check.button_pressed = _ajustes.texto_grande
	contraste_check.button_pressed = _ajustes.alto_contraste
	sonido_check.button_pressed = _ajustes.sonido

	efectos_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("efectos_reducidos", v))
	texto_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("texto_grande", v))
	contraste_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("alto_contraste", v))
	sonido_check.toggled.connect(func(v: bool) -> void: _cambiar_ajuste("sonido", v))


## Cambia el cuadradito de las casillas por una marca escrita, "[X]" o
## "[ ]", delante de su texto.
##
## El icono que trae el motor es un cuadro gris de contorno fino que sobre
## esta penumbra practicamente no se ve, y no hay forma de aclararlo desde
## el tema (el color de un icono solo puede multiplicarse, y multiplicar un
## gris oscuro no lo aclara). La marca escrita, en cambio, usa la misma
## tipografia que todo lo demas, crece con "texto grande" y aclara con
## "alto contraste" sin trabajo extra, ademas de sonar al hermano de
## terminal. El icono se tapa con una textura de un pixel transparente.
func _vestir_casillas() -> void:
	var invisible := _icono_invisible()
	for casilla in [duelo_check, efectos_check, texto_check, contraste_check, sonido_check]:
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


func _cambiar_ajuste(campo: String, valor: bool) -> void:
	_ajustes.set(campo, valor)
	_ajustes.guardar(ruta_ajustes)
	_aplicar_ajustes()


## Lleva los ajustes a quien los obedece. Se llama entera en cada cambio
## (son cuatro casillas, no hay nada que optimizar) para que no haya dos
## caminos distintos entre "cargar al arrancar" y "marcar en el menu".
func _aplicar_ajustes() -> void:
	fondo_taller.efectos_reducidos = _ajustes.efectos_reducidos
	vineta.efectos_reducidos = _ajustes.efectos_reducidos
	tambor.efectos_reducidos = _ajustes.efectos_reducidos
	tambor.alto_contraste = _ajustes.alto_contraste

	_aplicar_tamano_de_texto()
	_aplicar_contraste()

	if not _ajustes.sonido:
		sonido_ambiente.stop()
	elif not sonido_ambiente.playing:
		_arrancar_ambiente()
	else:
		_ajustar_volumen_ambiente()


func _aplicar_tamano_de_texto() -> void:
	var aumento := AUMENTO_TEXTO if _ajustes.texto_grande else 0
	if theme != null:
		theme.default_font_size = TAMANO_TEXTO + aumento
	for control in _tamanos_originales:
		var original: int = _tamanos_originales[control]
		control.add_theme_font_size_override("font_size", original + aumento)


func _aplicar_contraste() -> void:
	for control in _colores_originales:
		var original: Color = _colores_originales[control]
		control.add_theme_color_override("font_color", _con_contraste(original))

	# Botones, casillas y campos toman su color del tema, no de un override
	# nodo por nodo, asi que hay que subirlo tambien ahi.
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
	return color.lerp(Color.WHITE, MEZCLA_CONTRASTE) if _ajustes.alto_contraste else color


# --- Sonido -------------------------------------------------------------------


## Reproduce un efecto, salvo que el jugador haya quitado el sonido.
func _sonar(reproductor: AudioStreamPlayer) -> void:
	if _ajustes.sonido:
		reproductor.play()


## Arranca el bordon de ambiente, que suena en bucle mientras el juego este
## abierto (el archivo esta hecho a medida para encadenar sin costura: ver
## synth_sfx.ambiente).
##
## El bucle se marca aqui, sobre el flujo ya cargado, y no en el .import,
## porque el importador de WAV de Godot 4.7 no lo traslada al recurso:
## `edit/loop_mode` queda escrito en el .import pero el AudioStreamWAV
## cargado sigue diciendo LOOP_DISABLED. Es una modificacion en memoria del
## recurso importado —compartido, pero solo lo usa este reproductor— y por
## eso se hace una sola vez, comprobandolo antes.
##
## En headless (la CI y los tests) no se lanza: no hay dispositivo de audio
## que lo reproduzca, y una reproduccion en bucle no termina nunca por si
## sola, asi que seguiria viva al cerrarse el motor y Godot avisaria de
## recursos sin liberar (el "ERROR: resources still in use at exit" que la
## CI toma, con razon, por un fallo).
func _arrancar_ambiente() -> void:
	if not _ajustes.sonido or DisplayServer.get_name() == "headless":
		return
	var flujo := sonido_ambiente.stream as AudioStreamWAV
	if flujo != null and flujo.loop_mode != AudioStreamWAV.LOOP_FORWARD:
		flujo.loop_mode = AudioStreamWAV.LOOP_FORWARD
		flujo.loop_begin = 0
		flujo.loop_end = int(flujo.get_length() * flujo.mix_rate)

	sonido_ambiente.volume_db = VOLUMEN_AMBIENTE_MUDO
	sonido_ambiente.play()
	_ajustar_volumen_ambiente(2.0)


## Al cerrar el juego, corta el ambiente y le suelta el flujo. Es el unico
## sonido en bucle, o sea el unico que nunca termina por su cuenta.
##
## En una compilacion de depuracion el motor puede avisar igualmente al
## salir ("resources still in use at exit"): el servidor de audio descarta
## las reproducciones en su siguiente vuelta, que ya no llega. Es un aviso
## del log, sin efecto para quien juega, y no aparece en la CI porque en
## headless el ambiente ni se lanza (ver _arrancar_ambiente).
func _exit_tree() -> void:
	sonido_ambiente.stop()
	sonido_ambiente.stream = null


## Lleva el ambiente al volumen que toca segun donde estemos (menu o
## partida), con un fundido para que no de un salto.
func _ajustar_volumen_ambiente(duracion: float = 1.0) -> void:
	if not sonido_ambiente.playing:
		return
	var destino := VOLUMEN_AMBIENTE_PARTIDA if juego.visible else VOLUMEN_AMBIENTE_MENU
	var tween := create_tween()
	tween.tween_property(sonido_ambiente, "volume_db", destino, duracion)


# --- Menu previo a la partida -------------------------------------------------


func _mostrar_menu() -> void:
	menu.visible = true
	juego.visible = false
	etiqueta_records.text = _records.resumen()
	Maquina.completar(etiqueta_records)
	nombres_caja.visible = duelo_check.button_pressed
	fondo.color = COLOR_NORMAL
	sonido_ambiente.pitch_scale = 1.0
	_ajustar_volumen_ambiente()
	empezar_btn.grab_focus()


func _on_duelo_check_toggled(activado: bool) -> void:
	nombres_caja.visible = activado


## Nombre elegido para el jugador `numero`, o "Jugador N" si se dejo en
## blanco (mismo criterio que _pedir_nombre() en la version de terminal).
func _nombre_de(campo: LineEdit, numero: int) -> String:
	var escrito := campo.text.strip_edges()
	return escrito if escrito != "" else "Jugador %d" % numero


func _on_empezar_btn_pressed() -> void:
	var clave: String = Dificultad.ORDEN[dificultad_opt.selected]
	var nombres: Array[String] = []
	if duelo_check.button_pressed:
		nombres = [_nombre_de(nombre1, 1), _nombre_de(nombre2, 2)]

	menu.visible = false
	juego.visible = true
	_ajustar_volumen_ambiente()
	_estado.iniciar_juego(Dificultad.huecos_de(clave), Dificultad.marcas_de(clave), nombres)


# --- Acciones de la partida ---------------------------------------------------


func _on_disparar_btn_pressed() -> void:
	if _accion_bloqueada:
		return

	var numero := entrada_numero.text.to_int()
	if numero < 1 or numero > _estado.tambor.huecos:
		_estado.disparar(numero)  # deja que RuletaEstado emita entrada_invalida
		return

	_bloquear_acciones(true)
	_mostrar_resultado("...")
	_sonar(sonido_engranaje)
	await tambor.tension(numero)

	_ultimo_disparo = numero
	_mostrar_resultado("")
	_estado.disparar(numero)


func _on_marcar_btn_pressed() -> void:
	if _accion_bloqueada or not _estado.farol.puede_marcar():
		return

	var numero := entrada_numero.text.to_int()
	if numero < 1 or numero > _estado.tambor.huecos:
		_estado.marcar(numero)  # deja que RuletaEstado emita entrada_invalida
		return

	_bloquear_acciones(true)
	_mostrar_resultado("...")
	_sonar(sonido_engranaje)
	await tambor.tension(numero)

	_estado.marcar(numero)
	_bloquear_acciones(false)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_retirarse_btn_pressed() -> void:
	if _accion_bloqueada:
		return
	_bloquear_acciones(true)
	_estado.retirarse()


# --- Señales de RuletaEstado --------------------------------------------------


func _on_partida_iniciada(huecos: int, es_duelo: bool) -> void:
	_marcadas.clear()
	_resultados_farol.clear()
	_pistas_dudosas.clear()
	_proxima_pista_dudosa = false
	_ultimo_disparo = -1

	_mostrar_resultado("El tambor esta cargado. Elige una posicion y actua.")
	tambor.preparar_partida(huecos)
	_sonar(sonido_engranaje)
	tambor.girar()  # solo aqui: la bala no se re-sortea en cada disparo

	entrada_numero.clear()
	entrada_numero.placeholder_text = "Posicion del 1 al %d" % huecos
	entrada_numero.tooltip_text = entrada_numero.placeholder_text
	entrada_numero.grab_focus()

	etiqueta_turno.visible = es_duelo
	if es_duelo:
		var rival := _estado.jugadores[1]
		_refrescar_turno(_estado.jugador_activo.nombre, rival.nombre, rival.dias)

	_bloquear_acciones(false)
	_refrescar_cabecera()
	_refrescar_pistas()
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
			# El tambor se ha movido solo: se oye el engranaje y la
			# pantalla acusa el golpe.
			_sonar(sonido_engranaje)
			vineta.resplandor(COLOR_CLIC, 0.9)
			_vibrar_pantalla(0.02, 4, 0.25)
		"tambor_caliente":
			# La proxima pista puede ser mentira: la sala se pone al rojo
			# y el bordon se acelera hasta que el tambor se enfria.
			_proxima_pista_dudosa = true
			fondo_taller.calentar()
			vineta.resplandor(COLOR_CALOR, 1.6)
			_acelerar_ambiente()


func _on_pista_nueva(_texto: String, candidatos: Array) -> void:
	if _proxima_pista_dudosa:
		_pistas_dudosas.append(_estado.pistas_reveladas.size() - 1)
		_proxima_pista_dudosa = false
		tambor.destello(_a_huecos(candidatos))
	_refrescar_pistas()


func _on_disparo_sobrevivido(_disparos: int, en_juego: int) -> void:
	_marcadas.append(_ultimo_disparo)
	_agregar_linea_resultado("Click. Cartucho vacio. Lo apostado se dobla a %d puntos." % en_juego)
	tambor.aplicar_estados(_calcular_estados())
	tambor.pulsar()
	_sonar(sonido_disparo)
	_flash(COLOR_SUPERVIVENCIA)
	_refrescar_cabecera()
	_bloquear_acciones(false)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_dia_completado(dia: int) -> void:
	_agregar_linea_resultado("Sobrevives al dia %d." % dia)


func _on_farol_resuelto(hueco: int, acierto: bool, en_juego: int, marcas_restantes: int) -> void:
	if acierto:
		_mostrar_resultado(
			"Farol acertado: el hueco %d estaba vacio. +%d puntos."
			% [hueco, RuletaEstado.BONO_MARCA_ACERTADA]
		)
		_sonar(sonido_marca)
		_flash(COLOR_FAROL_ACIERTO)
	else:
		_mostrar_resultado("Farol fallido: ahi estaba la bala. Pierdes la marca.")
		_sonar(sonido_fallo)
		_flash(COLOR_FAROL_FALLO)

	_resultados_farol[hueco] = (
		TamborView.EstadoHueco.SEGURO if acierto else TamborView.EstadoHueco.PELIGRO
	)
	tambor.aplicar_estados(_calcular_estados())
	tambor.pulsar()
	_refrescar_cabecera()
	_actualizar_boton_marcar(marcas_restantes)


func _on_turno_cambiado(nombre: String, rival_nombre: String, rival_dias: int) -> void:
	_refrescar_turno(nombre, rival_nombre, rival_dias)
	_refrescar_cabecera()


func _on_impacto(disparos: int, perdidos: int, dias: int, resumen: String) -> void:
	var nuevo_record := _registrar_en_records(dias, perdidos)
	_mostrar_resultado(
		"BOOM. %sCaiste tras %d disparo(s) (%d dia(s) sobrevivido(s)), perdiendo %d puntos.\n%s"
		% [_prefijo_jugador(), disparos, dias, perdidos, resumen]
	)
	if nuevo_record:
		_agregar_linea_resultado("¡Nuevo record de dias sobrevividos!")

	if _ultimo_disparo != -1:
		var estados := _calcular_estados()
		estados[_ultimo_disparo] = TamborView.EstadoHueco.PELIGRO
		tambor.aplicar_estados(estados)
	_sonar(sonido_disparo)
	_sonar(sonido_derrota)
	_flash(COLOR_BOOM)
	vineta.resplandor(COLOR_CALOR, 1.2)
	_vibrar_pantalla()
	_cerrar_partida()


func _on_retirada(disparos: int, ganados: int, dias: int, resumen: String) -> void:
	var nuevo_record := _registrar_en_records(dias, ganados)
	_mostrar_resultado(
		"%sTe retira%s a tiempo. Cobra%s %d puntos tras %d disparo(s) (%d dia(s) sobrevivido(s)).\n%s"
		% [_prefijo_jugador(), "" if _estado.es_duelo() else "s",
			"" if _estado.es_duelo() else "s", ganados, disparos, dias, resumen]
	)
	if nuevo_record:
		_agregar_linea_resultado("¡Nuevo record de dias sobrevividos!")

	_sonar(sonido_victoria)
	_flash(COLOR_RETIRADA)
	_cerrar_partida()


## Solo en duelo, y siempre despues de impacto/retirada: añade el veredicto
## al mismo cartel de resultado antes de que _cerrar_partida() (que se
## difiere justo para esto) devuelva al menu.
func _on_duelo_terminado(jugadores: Array, ganadores: Array) -> void:
	_agregar_linea_resultado("")
	for jugador in jugadores:
		_agregar_linea_resultado(
			"%s: %d dia(s) sobrevividos, %d puntos."
			% [jugador.nombre, jugador.dias, jugador.puntos_finales]
		)
	if ganadores.size() == 1:
		_agregar_linea_resultado("¡Gana %s!" % ganadores[0].nombre)
	else:
		_agregar_linea_resultado("Empate. El tambor no se decide.")


# --- Fin de partida y records -------------------------------------------------


## Anota la partida del jugador activo (el que acaba de morir o
## retirarse) y devuelve si con ella ha batido su record de dias.
func _registrar_en_records(dias: int, puntos: int) -> bool:
	var nuevo_record := dias > _records.dias_maximos
	var bitacora := _estado.historial
	_records.registrar_partida(
		dias, puntos, bitacora.faroles_usados, bitacora.faroles_acertados
	)
	_records.guardar(ruta_records)
	return nuevo_record


## Nombre del jugador activo con el que empezar una frase, o "" en
## solitario (donde no hace falta decir de quien hablamos).
func _prefijo_jugador() -> String:
	return "%s: " % _estado.jugador_activo.nombre if _estado.es_duelo() else ""


## Cierra la partida y vuelve al menu. Se difiere a proposito: en duelo,
## `duelo_terminado` se emite justo despues de `impacto`/`retirada`, y
## asi el veredicto ya esta escrito en pantalla antes de que empiece la
## cuenta atras (ver _on_duelo_terminado).
func _cerrar_partida() -> void:
	_bloquear_acciones(true)
	_esperar_y_volver_al_menu.call_deferred()


func _esperar_y_volver_al_menu() -> void:
	await get_tree().create_timer(PAUSA_FIN_PARTIDA - DURACION_CIERRE).timeout
	await vineta.cerrar(DURACION_CIERRE)
	_mostrar_menu()
	vineta.abrir(DURACION_CIERRE)  # sin await: el menu ya esta puesto detras


# --- Utilidades de pintado ----------------------------------------------------


## Escribe el resultado del turno desde cero, tecleandolo como una maquina
## de escribir (ver Maquina.gd). `text` queda completo al instante: solo se
## anima cuanto de el se ve.
func _mostrar_resultado(texto: String) -> void:
	Maquina.escribir(etiqueta_resultado, texto, 0, _velocidad_tecleo())


## Añade `linea` al resultado del turno en curso, en una linea nueva si
## ya habia algo (p. ej. el texto de un evento antes del "Click..." que
## le sigue). Ver el orden de señales emitido por RuletaEstado.disparar().
## Lo ya escrito no se vuelve a teclear: sigue el mensaje donde iba.
func _agregar_linea_resultado(linea: String) -> void:
	var anterior := etiqueta_resultado.text
	if anterior == "":
		_mostrar_resultado(linea)
		return
	Maquina.escribir(
		etiqueta_resultado, anterior + "\n" + linea, anterior.length(), _velocidad_tecleo()
	)


## Con los efectos reducidos el texto aparece de golpe (ver Maquina.escribir).
func _velocidad_tecleo() -> float:
	return 0.0 if _ajustes.efectos_reducidos else Maquina.CARACTERES_POR_SEGUNDO


func _calcular_estados() -> Dictionary:
	var estados := {}
	for hueco in Pistas.interseccion(_estado.pistas_reveladas):
		estados[hueco] = TamborView.EstadoHueco.CANDIDATO
	for hueco in _marcadas:
		estados[hueco] = TamborView.EstadoHueco.PROBADO
	for hueco in _resultados_farol:
		estados[hueco] = _resultados_farol[hueco]
	return estados


## Convierte los candidatos de una pista (que viajan sin tipo en la señal,
## porque la misma señal la consume la version de terminal) en la lista de
## huecos tipada que espera TamborView.
func _a_huecos(candidatos: Array) -> Array[int]:
	var huecos: Array[int] = []
	for candidato in candidatos:
		huecos.append(int(candidato))
	return huecos


func _refrescar_turno(nombre: String, rival_nombre: String, rival_dias: int) -> void:
	etiqueta_turno.text = (
		"Turno de %s   ·   %s: %d dia(s) sobrevividos" % [nombre, rival_nombre, rival_dias]
	)


func _refrescar_cabecera() -> void:
	var dia := _estado.dias_sobrevividos() + 1
	var disparo_del_dia := _estado.disparos % RuletaEstado.DISPAROS_POR_DIA + 1
	etiqueta_cabecera.text = (
		"Dia %d (disparo %d/%d)  ·  Marcas %d  ·  En juego %d pts"
		% [
			dia, disparo_del_dia, RuletaEstado.DISPAROS_POR_DIA,
			_estado.farol.marcas_restantes, _estado.apuesta.en_juego,
		]
	)


## Reescribe la lista de pistas. Va dentro de un ScrollContainer de alto
## fijo porque el numero de pistas crece con cada disparo sobrevivido y sin
## tope acabaria empujando los botones fuera de la ventana; asi la columna
## mide siempre lo mismo y las pistas viejas siguen ahi, un poco mas arriba.
func _refrescar_pistas() -> void:
	if _estado.pistas_reveladas.is_empty():
		etiqueta_pistas.text = "La bala descansa en algun hueco. Aun no hay pistas."
		return
	var lineas: Array[String] = []
	for i in range(_estado.pistas_reveladas.size()):
		var marca := " (dudosa)" if _pistas_dudosas.has(i) else ""
		lineas.append("#%d %s%s" % [i + 1, _estado.pistas_reveladas[i].texto, marca])
	etiqueta_pistas.text = "\n".join(lineas)
	# La pista nueva es la ultima: se baja el scroll para que se vea sin
	# tocar nada. Diferido porque hasta el siguiente fotograma la etiqueta
	# no ha crecido y la barra aun no sabe cuanto puede bajar.
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
	_actualizar_boton_marcar(_estado.farol.marcas_restantes if not _estado.jugadores.is_empty() else 0)


## Tiñe el fondo un instante para subrayar lo que acaba de pasar. Con los
## efectos reducidos el color sigue siendo el mismo, pero entra y sale
## despacio: la informacion se mantiene y el parpadeo desaparece.
func _flash(color: Color) -> void:
	var entrada := 0.5 if _ajustes.efectos_reducidos else 0.15
	var salida := 0.9 if _ajustes.efectos_reducidos else 0.6
	var tween := create_tween()
	tween.tween_property(fondo, "color", color, entrada)
	tween.tween_property(fondo, "color", COLOR_NORMAL, salida)


## Sacudida de la pantalla al morir: pequenos bandazos de rotacion sobre
## el contenido (no sobre Fondo, que al ser un color solido no se veria
## mover). Rotar en vez de mover no interfiere con los anchors a
## pantalla completa de Centro (ver TamborView.girar(), que usa el
## mismo truco para el giro del tambor).
func _vibrar_pantalla(intensidad: float = 0.05, sacudidas: int = 6, duracion: float = 0.35) -> void:
	if _ajustes.efectos_reducidos:
		return
	var tramo := duracion / float(sacudidas)
	var tween := create_tween()
	for _i in range(sacudidas):
		tween.tween_property(centro, "rotation", randf_range(-intensidad, intensidad), tramo)
	tween.tween_property(centro, "rotation", 0.0, tramo)


## Acelera el bordon mientras el tambor esta caliente y lo devuelve a su
## ritmo al mismo tiempo que FondoTaller se enfria.
func _acelerar_ambiente() -> void:
	if not sonido_ambiente.playing:
		return
	var tween := create_tween()
	tween.tween_property(sonido_ambiente, "pitch_scale", PITCH_AMBIENTE_CALIENTE, 0.4)
	tween.tween_property(sonido_ambiente, "pitch_scale", 1.0, FondoTaller.ENFRIAMIENTO)
