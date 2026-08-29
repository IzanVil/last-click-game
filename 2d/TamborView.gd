extends Control
class_name TamborView
## Vista del tambor: dibuja los huecos en corona y anima el giro (solo al
## empezar partida), la tension antes de revelar un disparo o un farol,
## y un pequeno pulso al resolverlos.
##
## No conoce reglas del juego (bala, apuestas, dias...): solo pinta el
## estado que le pasa MainGame.gd via aplicar_estados(), espejo de
## calcular_estados()/dibujar_tambor() en terminal/ruleta.py.

const RADIO_TAMBOR := 90.0
const RADIO_HUECO := 18.0

## Paleta noir/steampunk: metal envejecido y laton en penumbra, en vez
## del verde/rojo "de manual" de la mecanica anterior.
const COLOR_DESCONOCIDO := Color(0.16, 0.15, 0.14, 1)  # hierro en sombra
const COLOR_PROBADO := Color(0.32, 0.30, 0.27, 1)  # metal deslustrado
const COLOR_CANDIDATO := Color(0.78, 0.58, 0.16, 1)  # laton encendido
const COLOR_SEGURO := Color(0.24, 0.47, 0.34, 1)  # cardenillo
const COLOR_PELIGRO := Color(0.62, 0.11, 0.11, 1)  # sangre seca
const COLOR_BORDE := Color(0.03, 0.02, 0.02, 1)
const COLOR_TEXTO := Color(0.92, 0.86, 0.74, 1)  # pergamino
const COLOR_ANILLO := Color(0.55, 0.42, 0.18, 1)  # laton
const COLOR_TENSION := Color(0.95, 0.75, 0.25, 1)  # laton encendido

## Estados posibles de un hueco. Coinciden 1 a 1 con los cuatro que
## calcular_estados() usa en la version de terminal, mas DESCONOCIDO
## (huecos de los que aun no se sabe nada, sin equivalente ahi porque
## esa version simplemente no los marca).
enum EstadoHueco { DESCONOCIDO, PROBADO, CANDIDATO, SEGURO, PELIGRO }

var _num_huecos := 8
var _estados: Array[EstadoHueco] = []

## Hueco (0-indexado) que esta "en tension": ya se disparo o marco pero
## el resultado aun no se ha revelado. -1 = ninguno.
var _hueco_tension := -1
var _pulso_tension := 0.0


func _ready() -> void:
	custom_minimum_size = Vector2((RADIO_TAMBOR + RADIO_HUECO) * 2, (RADIO_TAMBOR + RADIO_HUECO) * 2)
	resized.connect(func() -> void: pivot_offset = size / 2.0)
	pivot_offset = size / 2.0


## Resetea todos los huecos a "desconocido" para una partida nueva.
func preparar_partida(num_huecos: int) -> void:
	_num_huecos = num_huecos
	_estados.resize(num_huecos)
	_estados.fill(EstadoHueco.DESCONOCIDO)
	queue_redraw()


## Reemplaza el estado de todos los huecos a la vez (indexados 1..N, tal
## como los maneja el resto del juego). Espejo de dibujar_tambor() en
## terminal/ruleta.py: quien no aparece en `estados` se pinta como
## "desconocido".
func aplicar_estados(estados: Dictionary) -> void:
	for i in range(_num_huecos):
		_estados[i] = estados.get(i + 1, EstadoHueco.DESCONOCIDO)
	queue_redraw()


## Gira el tambor un numero entero de vueltas (asi siempre se asienta con
## los huecos en su sitio). Solo tiene sentido al cargar una partida
## nueva: a diferencia de la mecanica anterior, la bala no se
## re-sortea en cada disparo, asi que girar el tambor entero en cada
## turno insinuaria un azar que ya no existe.
func girar(duracion: float = 0.7) -> void:
	var vueltas := 2 + randi_range(0, 2)
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "rotation", rotation + TAU * vueltas, duracion)
	await tween.finished


## Late en torno al hueco elegido antes de revelar un disparo o un
## farol: el resultado ya esta decidido, pero la vista retrasa el
## reveal un instante y pulsa un halo de laton para meter tension.
## Quien llama debe esperar (await) antes de aplicar el resultado real.
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


## Pequeno pulso de escala para resaltar que el tambor acaba de
## cambiar (disparo o farol resueltos). Puramente decorativo.
func pulsar() -> void:
	var tween := create_tween()
	tween.tween_property(self, "scale", Vector2(1.15, 1.15), 0.08)
	tween.tween_property(self, "scale", Vector2.ONE, 0.15)


func _draw() -> void:
	if _num_huecos <= 0:
		return

	var centro := size / 2.0
	draw_arc(centro, RADIO_TAMBOR + RADIO_HUECO * 0.6, 0, TAU, 48, COLOR_ANILLO, 3.0)

	var font := get_theme_default_font()
	var font_size := 16

	for i in range(_num_huecos):
		var angulo := -PI / 2.0 + i * TAU / _num_huecos
		var pos := centro + Vector2(cos(angulo), sin(angulo)) * RADIO_TAMBOR
		var color := _color_de(_estados[i])

		draw_circle(pos, RADIO_HUECO, color)
		draw_arc(pos, RADIO_HUECO, 0, TAU, 24, COLOR_BORDE, 2.0)

		if i == _hueco_tension:
			var radio_halo := RADIO_HUECO + 4.0 + _pulso_tension * 8.0
			var color_halo := COLOR_TENSION
			color_halo.a = 0.35 + _pulso_tension * 0.65
			draw_arc(pos, radio_halo, 0, TAU, 24, color_halo, 3.0)

		var texto := str(i + 1)
		var text_size := font.get_string_size(texto, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size)
		draw_string(
			font, pos - text_size / 2.0 + Vector2(0, text_size.y * 0.35),
			texto, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size, COLOR_TEXTO
		)


func _color_de(estado_hueco: EstadoHueco) -> Color:
	match estado_hueco:
		EstadoHueco.PROBADO:
			return COLOR_PROBADO
		EstadoHueco.CANDIDATO:
			return COLOR_CANDIDATO
		EstadoHueco.SEGURO:
			return COLOR_SEGURO
		EstadoHueco.PELIGRO:
			return COLOR_PELIGRO
		_:
			return COLOR_DESCONOCIDO
