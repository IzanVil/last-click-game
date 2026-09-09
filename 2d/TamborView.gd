class_name TamborView
extends Control
## Vista del tambor de la ruleta: dibuja los huecos en corona, deja
## pulsarlos y anima el giro y el revelado de un disparo. No conoce reglas
## del juego (rondas, balas, condicion de victoria): solo pinta los
## estados que le pasa MainGame.gd y avisa de que se pulso un hueco.

## Se emite al pulsar un hueco con el raton, con su numero 1-indexado
## (el mismo que se ve dibujado). Quien escuche decide si ese disparo
## procede: aqui no se sabe si la partida esta bloqueada.
signal hueco_pulsado(numero: int)

enum EstadoHueco {
	OCULTO,  ## Aun sin disparar.
	VACIO,  ## Se disparo y estaba vacio.
	BALA_FATAL,  ## La bala que alcanzo al jugador.
	BALA,  ## Otra bala del tambor, destapada al perder.
}

const RADIO_TAMBOR := 90.0
const RADIO_HUECO := 18.0

const COLOR_HUECO_OCULTO := Color(0.35, 0.35, 0.4, 1)
const COLOR_HUECO_BALA_FATAL := Color(0.85, 0.15, 0.15, 1)
const COLOR_HUECO_BALA := Color(0.45, 0.13, 0.13, 1)
const COLOR_HUECO_VACIO := Color(0.2, 0.75, 0.35, 1)
const COLOR_BORDE := Color(0.05, 0.05, 0.08, 1)
const COLOR_TEXTO := Color(0.95, 0.95, 0.95, 1)
const COLOR_ANILLO := Color(0.5, 0.45, 0.15, 1)
const COLOR_TENSION := Color(0.95, 0.85, 0.25, 1)
const COLOR_HOVER := Color(0.95, 0.95, 0.95, 0.75)

var _num_huecos := 10
var _estados: Array[int] = []

## Hueco (0-indexado) que esta "en tension": el jugador ya disparo pero
## el resultado aun no se ha revelado. -1 = ninguno.
var _hueco_tension := -1
var _pulso_tension := 0.0

## Hueco (1-indexado) bajo el raton, para resaltarlo. -1 = ninguno.
var _hueco_hover := -1

## True mientras girar() esta en marcha. Los numeros se mueven bajo el
## cursor, asi que en ese rato no se aceptan clicks (ver _gui_input).
var _girando := false


func _ready() -> void:
	custom_minimum_size = Vector2(
		(RADIO_TAMBOR + RADIO_HUECO) * 2, (RADIO_TAMBOR + RADIO_HUECO) * 2
	)
	resized.connect(func(): pivot_offset = size / 2.0)
	pivot_offset = size / 2.0
	mouse_exited.connect(_olvidar_hover)


## Centro de un hueco (0-indexado) en coordenadas locales.
##
## La usan tanto _draw() como hueco_en(): comparten la geometria a
## proposito, para que lo que se ve dibujado y lo que se puede pulsar no
## puedan separarse si algun dia cambian los radios o el reparto en
## corona.
func centro_hueco(indice: int) -> Vector2:
	var angulo := -PI / 2.0 + indice * TAU / _num_huecos
	return size / 2.0 + Vector2(cos(angulo), sin(angulo)) * RADIO_TAMBOR


## Numero de hueco (1-indexado) bajo `punto`, en coordenadas locales del
## nodo, o -1 si el punto no cae dentro de ninguno. El centro del tambor
## y las esquinas del rectangulo no son de nadie.
func hueco_en(punto: Vector2) -> int:
	for indice in range(_num_huecos):
		if punto.distance_to(centro_hueco(indice)) <= RADIO_HUECO:
			return indice + 1
	return -1


## Estado que esta mostrando el hueco `numero` (1-indexado), u OCULTO si
## ese numero no existe en el tambor actual.
func estado_hueco(numero: int) -> EstadoHueco:
	var indice := numero - 1
	if indice < 0 or indice >= _estados.size():
		return EstadoHueco.OCULTO
	return _estados[indice] as EstadoHueco


func _gui_input(evento: InputEvent) -> void:
	if evento is InputEventMouseMotion:
		_actualizar_hover(hueco_en((evento as InputEventMouseMotion).position))
		return

	var boton := evento as InputEventMouseButton
	if boton == null or boton.button_index != MOUSE_BUTTON_LEFT or not boton.pressed:
		return
	# Mientras el tambor gira, los huecos se mueven bajo el cursor: dar
	# por bueno el click seria disparar a un numero distinto del que el
	# jugador creia estar pulsando.
	if _girando:
		return

	var numero := hueco_en(boton.position)
	if numero != -1:
		accept_event()
		hueco_pulsado.emit(numero)


func _actualizar_hover(numero: int) -> void:
	if numero == _hueco_hover:
		return
	_hueco_hover = numero
	mouse_default_cursor_shape = CURSOR_POINTING_HAND if numero != -1 else CURSOR_ARROW
	queue_redraw()


func _olvidar_hover() -> void:
	_actualizar_hover(-1)


## Resetea todos los huecos a "oculto" para una ronda nueva. Se llama al
## recibir ronda_preparada, antes de que el jugador pueda disparar.
func preparar_ronda(num_huecos: int) -> void:
	_num_huecos = num_huecos
	_estados.resize(num_huecos)
	_estados.fill(EstadoHueco.OCULTO)
	queue_redraw()


## Gira el tambor un numero entero de vueltas (asi siempre se asienta con
## los huecos en su sitio, aunque a mitad de giro se vea girar de verdad).
## No decide el resultado: eso ya lo resolvio RuletaEstado antes de llamar
## a revelar(). Es puro adorno para dar tension antes del disparo.
func girar(duracion: float = 0.7) -> void:
	_girando = true
	var vueltas := 2 + randi_range(0, 2)
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "rotation", rotation + TAU * vueltas, duracion)
	await tween.finished
	_girando = false


## Late en torno al hueco elegido antes de revelar el resultado: el
## disparo ya esta decidido en RuletaEstado, pero la vista retrasa el
## reveal un instante y pulsa un halo amarillo para meter tension, en
## vez de mostrar el resultado al momento. Quien llama debe esperar a
## que termine (await) antes de pedir el reveal real con revelar().
func tension(numero: int, duracion: float = 0.5) -> void:
	_hueco_tension = numero - 1
	queue_redraw()

	var tramo := duracion / 6.0
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.set_loops(3)
	tween.tween_method(_set_pulso_tension, 0.0, 1.0, tramo)
	tween.tween_method(_set_pulso_tension, 1.0, 0.0, tramo)
	await tween.finished

	_hueco_tension = -1
	queue_redraw()


func _set_pulso_tension(valor: float) -> void:
	_pulso_tension = valor
	queue_redraw()


## Marca el hueco que acaba de disparar el jugador (`numero` 1-indexado,
## como lo ve en pantalla) y lo resalta con un pulso de escala. Si habia
## bala queda como BALA_FATAL, que se pinta mas viva que las demas para
## que se distinga de las que destapa revelar_balas().
func revelar(numero: int, es_bala: bool) -> void:
	var indice := numero - 1
	if indice < 0 or indice >= _estados.size():
		return
	_estados[indice] = EstadoHueco.BALA_FATAL if es_bala else EstadoHueco.VACIO
	queue_redraw()

	var tween := create_tween()
	tween.tween_property(self, "scale", Vector2(1.15, 1.15), 0.08)
	tween.tween_property(self, "scale", Vector2.ONE, 0.15)


## Destapa el resto del tambor al perder, para que se vea lo cerca (o lo
## lejos) que se estuvo. No pisa lo ya revelado: el hueco fatal sigue
## siendo BALA_FATAL y los vacios acertados siguen verdes.
func revelar_balas(balas: Array[int]) -> void:
	for numero in balas:
		var indice := numero - 1
		if indice < 0 or indice >= _estados.size():
			continue
		if _estados[indice] == EstadoHueco.OCULTO:
			_estados[indice] = EstadoHueco.BALA
	queue_redraw()


func _draw() -> void:
	if _num_huecos <= 0:
		return

	var centro := size / 2.0
	draw_arc(centro, RADIO_TAMBOR + RADIO_HUECO * 0.6, 0, TAU, 48, COLOR_ANILLO, 3.0)

	var font := get_theme_default_font()
	var font_size := 16

	for i in range(_num_huecos):
		var pos := centro_hueco(i)
		var color := COLOR_HUECO_OCULTO
		match _estados[i]:
			EstadoHueco.BALA_FATAL:
				color = COLOR_HUECO_BALA_FATAL
			EstadoHueco.BALA:
				color = COLOR_HUECO_BALA
			EstadoHueco.VACIO:
				color = COLOR_HUECO_VACIO

		draw_circle(pos, RADIO_HUECO, color)
		draw_arc(pos, RADIO_HUECO, 0, TAU, 24, COLOR_BORDE, 2.0)

		if i + 1 == _hueco_hover and _estados[i] == EstadoHueco.OCULTO:
			draw_arc(pos, RADIO_HUECO + 3.0, 0, TAU, 24, COLOR_HOVER, 2.0)

		if i == _hueco_tension:
			var radio_halo := RADIO_HUECO + 4.0 + _pulso_tension * 8.0
			var color_halo := COLOR_TENSION
			color_halo.a = 0.35 + _pulso_tension * 0.65
			draw_arc(pos, radio_halo, 0, TAU, 24, color_halo, 3.0)

		var texto := str(i + 1)
		var text_size := font.get_string_size(texto, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size)
		draw_string(
			font,
			pos - text_size / 2.0 + Vector2(0, text_size.y * 0.35),
			texto,
			HORIZONTAL_ALIGNMENT_CENTER,
			-1,
			font_size,
			COLOR_TEXTO
		)
