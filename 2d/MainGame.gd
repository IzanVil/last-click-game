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

const COLOR_NORMAL := Color(0.09, 0.08, 0.07, 1)
const COLOR_BOOM := Color(0.42, 0.05, 0.05, 1)
const COLOR_SUPERVIVENCIA := Color(0.2, 0.16, 0.06, 1)
const COLOR_FAROL_ACIERTO := Color(0.08, 0.22, 0.14, 1)
const COLOR_FAROL_FALLO := Color(0.3, 0.07, 0.07, 1)
const COLOR_RETIRADA := Color(0.12, 0.2, 0.13, 1)
const COLOR_RECORD := Color(0.78, 0.58, 0.16, 1)

## Cuanto se queda en pantalla el resultado final antes de volver al menu.
const PAUSA_FIN_PARTIDA := 2.6

@onready var fondo: ColorRect = $Fondo
@onready var centro: CenterContainer = $Centro

@onready var menu: VBoxContainer = $Centro/Columnas/Menu
@onready var etiqueta_records: Label = $Centro/Columnas/Menu/Records
@onready var dificultad_opt: OptionButton = $Centro/Columnas/Menu/DificultadFila/DificultadOpt
@onready var duelo_check: CheckBox = $Centro/Columnas/Menu/DueloCheck
@onready var nombres_caja: VBoxContainer = $Centro/Columnas/Menu/Nombres
@onready var nombre1: LineEdit = $Centro/Columnas/Menu/Nombres/Nombre1
@onready var nombre2: LineEdit = $Centro/Columnas/Menu/Nombres/Nombre2
@onready var empezar_btn: Button = $Centro/Columnas/Menu/EmpezarBtn

@onready var juego: VBoxContainer = $Centro/Columnas/Juego
@onready var etiqueta_turno: Label = $Centro/Columnas/Juego/Turno
@onready var etiqueta_cabecera: Label = $Centro/Columnas/Juego/Cabecera
@onready var etiqueta_pistas: Label = $Centro/Columnas/Juego/Pistas
@onready var etiqueta_resultado: Label = $Centro/Columnas/Juego/Resultado
@onready var entrada_numero: LineEdit = $Centro/Columnas/Juego/EntradaNumero
@onready var disparar_btn: Button = $Centro/Columnas/Juego/Botones/DispararBtn
@onready var marcar_btn: Button = $Centro/Columnas/Juego/Botones/MarcarBtn
@onready var retirarse_btn: Button = $Centro/Columnas/Juego/Botones/RetirarseBtn
@onready var tambor: TamborView = $Centro/Columnas/Juego/Tambor

@onready var sonido_disparo: AudioStreamPlayer = $SonidoDisparo
@onready var sonido_victoria: AudioStreamPlayer = $SonidoVictoria
@onready var sonido_derrota: AudioStreamPlayer = $SonidoDerrota

var _estado := RuletaEstado.new()
var _records := Records.new()

## Archivo donde se leen y guardan los records. Es una variable, y no la
## constante Records.RUTA_POR_DEFECTO usada directamente, para que los
## tests puedan redirigirla (antes de add_child, o sea antes de _ready)
## y no pisar los records reales de quien los ejecute. Mismo motivo que
## RuletaEstado.probabilidad_eventos.
var ruta_records := Records.RUTA_POR_DEFECTO

## Huecos ya disparados (gris) y resultados de farol por hueco (verde o
## rojo, ver TamborView.EstadoHueco). Igual que en terminal/ruleta.py,
## esto no vive en la logica pura: es memoria de la vista. En duelo son
## compartidos, como el propio tambor.
var _marcadas: Array[int] = []
var _resultados_farol: Dictionary = {}

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


func _ready() -> void:
	randomize()
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

	_records = Records.cargar(ruta_records)
	_mostrar_menu()


# --- Menu previo a la partida -------------------------------------------------


func _mostrar_menu() -> void:
	menu.visible = true
	juego.visible = false
	etiqueta_records.text = _records.resumen()
	nombres_caja.visible = duelo_check.button_pressed
	fondo.color = COLOR_NORMAL
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
	etiqueta_resultado.text = "..."
	await tambor.tension(numero)

	_ultimo_disparo = numero
	etiqueta_resultado.text = ""
	_estado.disparar(numero)


func _on_marcar_btn_pressed() -> void:
	if _accion_bloqueada or not _estado.farol.puede_marcar():
		return

	var numero := entrada_numero.text.to_int()
	if numero < 1 or numero > _estado.tambor.huecos:
		_estado.marcar(numero)  # deja que RuletaEstado emita entrada_invalida
		return

	_bloquear_acciones(true)
	etiqueta_resultado.text = "..."
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
	_ultimo_disparo = -1

	etiqueta_resultado.text = "El tambor esta cargado. Elige una posicion y actua."
	tambor.preparar_partida(huecos)
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
	etiqueta_resultado.text = (
		"Ese numero no esta en el tambor. Elige entre 1 y %d." % _estado.tambor.huecos
	)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_evento_ocurrido(_tipo: String, texto: String) -> void:
	_agregar_linea_resultado(texto)


func _on_pista_nueva(_texto: String, _candidatos: Array) -> void:
	_refrescar_pistas()


func _on_disparo_sobrevivido(_disparos: int, en_juego: int) -> void:
	_marcadas.append(_ultimo_disparo)
	_agregar_linea_resultado("Click. Cartucho vacio. Lo apostado se dobla a %d puntos." % en_juego)
	tambor.aplicar_estados(_calcular_estados())
	tambor.pulsar()
	sonido_disparo.play()
	_flash(COLOR_SUPERVIVENCIA)
	_refrescar_cabecera()
	_bloquear_acciones(false)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_dia_completado(dia: int) -> void:
	_agregar_linea_resultado("Sobrevives al dia %d." % dia)


func _on_farol_resuelto(hueco: int, acierto: bool, en_juego: int, marcas_restantes: int) -> void:
	if acierto:
		etiqueta_resultado.text = (
			"Farol acertado: el hueco %d estaba vacio. +%d puntos."
			% [hueco, RuletaEstado.BONO_MARCA_ACERTADA]
		)
		_flash(COLOR_FAROL_ACIERTO)
	else:
		etiqueta_resultado.text = "Farol fallido: ahi estaba la bala. Pierdes la marca."
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
	etiqueta_resultado.text = (
		"BOOM. %sCaiste tras %d disparo(s) (%d dia(s) sobrevivido(s)), perdiendo %d puntos.\n%s"
		% [_prefijo_jugador(), disparos, dias, perdidos, resumen]
	)
	if nuevo_record:
		_agregar_linea_resultado("¡Nuevo record de dias sobrevividos!")

	if _ultimo_disparo != -1:
		var estados := _calcular_estados()
		estados[_ultimo_disparo] = TamborView.EstadoHueco.PELIGRO
		tambor.aplicar_estados(estados)
	sonido_disparo.play()
	sonido_derrota.play()
	_flash(COLOR_BOOM)
	_vibrar_pantalla()
	_cerrar_partida()


func _on_retirada(disparos: int, ganados: int, dias: int, resumen: String) -> void:
	var nuevo_record := _registrar_en_records(dias, ganados)
	etiqueta_resultado.text = (
		"%sTe retira%s a tiempo. Cobra%s %d puntos tras %d disparo(s) (%d dia(s) sobrevivido(s)).\n%s"
		% [_prefijo_jugador(), "" if _estado.es_duelo() else "s",
			"" if _estado.es_duelo() else "s", ganados, disparos, dias, resumen]
	)
	if nuevo_record:
		_agregar_linea_resultado("¡Nuevo record de dias sobrevividos!")

	sonido_victoria.play()
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
	await get_tree().create_timer(PAUSA_FIN_PARTIDA).timeout
	_mostrar_menu()


# --- Utilidades de pintado ----------------------------------------------------


## Añade `linea` al resultado del turno en curso, en una linea nueva si
## ya habia algo (p. ej. el texto de un evento antes del "Click..." que
## le sigue). Ver el orden de señales emitido por RuletaEstado.disparar().
func _agregar_linea_resultado(linea: String) -> void:
	if etiqueta_resultado.text == "":
		etiqueta_resultado.text = linea
	else:
		etiqueta_resultado.text += "\n" + linea


func _calcular_estados() -> Dictionary:
	var estados := {}
	for hueco in Pistas.interseccion(_estado.pistas_reveladas):
		estados[hueco] = TamborView.EstadoHueco.CANDIDATO
	for hueco in _marcadas:
		estados[hueco] = TamborView.EstadoHueco.PROBADO
	for hueco in _resultados_farol:
		estados[hueco] = _resultados_farol[hueco]
	return estados


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


func _refrescar_pistas() -> void:
	if _estado.pistas_reveladas.is_empty():
		etiqueta_pistas.text = "La bala descansa en algun hueco. Aun no hay pistas."
		return
	var lineas: Array[String] = []
	for i in range(_estado.pistas_reveladas.size()):
		lineas.append("#%d %s" % [i + 1, _estado.pistas_reveladas[i].texto])
	etiqueta_pistas.text = "\n".join(lineas)


func _actualizar_boton_marcar(marcas_restantes: int) -> void:
	marcar_btn.text = "Marcar (%d)" % marcas_restantes
	marcar_btn.disabled = _accion_bloqueada or marcas_restantes <= 0


func _bloquear_acciones(bloqueada: bool) -> void:
	_accion_bloqueada = bloqueada
	entrada_numero.editable = not bloqueada
	disparar_btn.disabled = bloqueada
	retirarse_btn.disabled = bloqueada
	_actualizar_boton_marcar(_estado.farol.marcas_restantes if not _estado.jugadores.is_empty() else 0)


func _flash(color: Color) -> void:
	var tween := create_tween()
	tween.tween_property(fondo, "color", color, 0.15)
	tween.tween_property(fondo, "color", COLOR_NORMAL, 0.6)


## Sacudida de la pantalla al morir: pequenos bandazos de rotacion sobre
## el contenido (no sobre Fondo, que al ser un color solido no se veria
## mover). Rotar en vez de mover no interfiere con los anchors a
## pantalla completa de Centro (ver TamborView.girar(), que usa el
## mismo truco para el giro del tambor).
func _vibrar_pantalla(intensidad: float = 0.05, sacudidas: int = 6, duracion: float = 0.35) -> void:
	var tramo := duracion / float(sacudidas)
	var tween := create_tween()
	for _i in range(sacudidas):
		tween.tween_property(centro, "rotation", randf_range(-intensidad, intensidad), tramo)
	tween.tween_property(centro, "rotation", 0.0, tramo)
