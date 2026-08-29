extends Control
## Vista de "El Tambor del Juicio": escucha las señales de RuletaEstado
## y actualiza Label/ColorRect/Tween/TamborView en pantalla.
##
## No conoce reglas del juego (bala, apuestas, farol, dias... viven en
## RuletaEstado y los modulos que orquesta). Hermano de terminal/ruleta.py:
## misma separacion entre logica pura e interfaz, misma orquestacion de
## disparar/marcar/retirarse, adaptada de teclado+colores ANSI a
## botones+Tween.

const COLOR_NORMAL := Color(0.09, 0.08, 0.07, 1)
const COLOR_BOOM := Color(0.42, 0.05, 0.05, 1)
const COLOR_SUPERVIVENCIA := Color(0.2, 0.16, 0.06, 1)
const COLOR_FAROL_ACIERTO := Color(0.08, 0.22, 0.14, 1)
const COLOR_FAROL_FALLO := Color(0.3, 0.07, 0.07, 1)
const COLOR_RETIRADA := Color(0.12, 0.2, 0.13, 1)

@onready var fondo: ColorRect = $Fondo
@onready var centro: CenterContainer = $Centro
@onready var etiqueta_cabecera: Label = $Centro/Columnas/Cabecera
@onready var etiqueta_pistas: Label = $Centro/Columnas/Pistas
@onready var etiqueta_resultado: Label = $Centro/Columnas/Resultado
@onready var entrada_numero: LineEdit = $Centro/Columnas/EntradaNumero
@onready var disparar_btn: Button = $Centro/Columnas/Botones/DispararBtn
@onready var marcar_btn: Button = $Centro/Columnas/Botones/MarcarBtn
@onready var retirarse_btn: Button = $Centro/Columnas/Botones/RetirarseBtn
@onready var tambor: TamborView = $Centro/Columnas/Tambor
@onready var sonido_disparo: AudioStreamPlayer = $SonidoDisparo
@onready var sonido_victoria: AudioStreamPlayer = $SonidoVictoria
@onready var sonido_derrota: AudioStreamPlayer = $SonidoDerrota

var _estado := RuletaEstado.new()

## Huecos ya disparados (gris) y resultados de farol por hueco (verde o
## rojo, ver TamborView.EstadoHueco). Igual que en terminal/ruleta.py,
## esto no vive en la logica pura: es memoria de la vista.
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
	entrada_numero.text_submitted.connect(func(_texto: String) -> void: _on_disparar_btn_pressed())
	centro.pivot_offset = centro.size / 2.0
	centro.resized.connect(func() -> void: centro.pivot_offset = centro.size / 2.0)
	_estado.iniciar_juego()


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


func _on_partida_iniciada(huecos: int) -> void:
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


func _on_impacto(disparos: int, perdidos: int, dias: int, resumen: String) -> void:
	etiqueta_resultado.text = (
		"BOOM. Caiste tras %d disparo(s) (%d dia(s) sobrevivido(s)), perdiendo %d puntos.\n%s"
		% [disparos, dias, perdidos, resumen]
	)
	if _ultimo_disparo != -1:
		var estados := _calcular_estados()
		estados[_ultimo_disparo] = TamborView.EstadoHueco.PELIGRO
		tambor.aplicar_estados(estados)
	sonido_disparo.play()
	sonido_derrota.play()
	_flash(COLOR_BOOM)
	await _vibrar_pantalla()
	await get_tree().create_timer(1.6).timeout
	_estado.iniciar_juego()


func _on_retirada(disparos: int, ganados: int, dias: int, resumen: String) -> void:
	etiqueta_resultado.text = (
		"Te retiras a tiempo. Cobras %d puntos tras %d disparo(s) (%d dia(s) sobrevivido(s)).\n%s"
		% [ganados, disparos, dias, resumen]
	)
	sonido_victoria.play()
	_flash(COLOR_RETIRADA)
	await get_tree().create_timer(2.5).timeout
	_estado.iniciar_juego()


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
	_actualizar_boton_marcar(_estado.farol.marcas_restantes if _estado.farol else 0)


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
	await tween.finished
