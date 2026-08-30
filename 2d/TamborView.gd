extends Control
class_name TamborView
## Vista del tambor: dibuja la rueda de huecos con su chapa, sus remaches y
## su eje, y anima el giro (solo al empezar partida), la tension antes de
## revelar un disparo o un farol, el latido de los huecos candidatos y un
## pequeno pulso al resolverlos.
##
## No conoce reglas del juego (bala, apuestas, dias...): solo pinta el
## estado que le pasa MainGame.gd via aplicar_estados(), espejo de
## calcular_estados()/dibujar_tambor() en terminal/ruleta.py.
##
## Todo esta dibujado con `_draw()`, sin sprites ni modelo 3D: el tambor
## cambia de numero de huecos con la dificultad (6, 8 o 10), asi que una
## corona calculada sale mas barata y siempre encaja, mientras que un sprite
## habria que tenerlo en tres versiones.

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
const COLOR_CHAPA := Color(0.13, 0.12, 0.11, 1)  # la placa del tambor
const COLOR_SOMBRA := Color(0, 0, 0, 0.45)

## Estados posibles de un hueco. Coinciden 1 a 1 con los cuatro que
## calcular_estados() usa en la version de terminal, mas DESCONOCIDO
## (huecos de los que aun no se sabe nada, sin equivalente ahi porque
## esa version simplemente no los marca).
enum EstadoHueco { DESCONOCIDO, PROBADO, CANDIDATO, SEGURO, PELIGRO }

## Misma paleta subida de tono para el ajuste de alto contraste: los mismos
## cinco estados, pero legibles sin depender de la penumbra (ver
## Ajustes.alto_contraste). El significado de cada color no cambia.
const PALETA_CONTRASTE := {
	EstadoHueco.DESCONOCIDO: Color(0.35, 0.35, 0.35, 1),
	EstadoHueco.PROBADO: Color(0.68, 0.68, 0.66, 1),
	EstadoHueco.CANDIDATO: Color(1.0, 0.80, 0.15, 1),
	EstadoHueco.SEGURO: Color(0.25, 0.85, 0.45, 1),
	EstadoHueco.PELIGRO: Color(1.0, 0.25, 0.20, 1),
}

## Con los efectos reducidos se queda quieto todo lo que late o vibra por
## si solo (el latido de los candidatos); lo que responde a una accion del
## jugador (giro, tension, pulso) se mantiene, porque ahi la animacion no
## es adorno: es la respuesta a lo que acaba de hacer.
var efectos_reducidos := false:
	set(valor):
		efectos_reducidos = valor
		_actualizar_latido()

var alto_contraste := false:
	set(valor):
		alto_contraste = valor
		queue_redraw()

var _num_huecos := 8
var _estados: Array[EstadoHueco] = []

## Hueco (0-indexado) que esta "en tension": ya se disparo o marco pero
## el resultado aun no se ha revelado. -1 = ninguno.
var _hueco_tension := -1
var _pulso_tension := 0.0

## Reloj propio del latido de los candidatos. Solo avanza mientras hay
## alguno que late (ver _actualizar_latido).
var _tiempo := 0.0

## Huecos que estan dando un destello (ver destello()) y su opacidad.
var _huecos_destello: Array[int] = []
var _destello_alfa := 0.0:
	set(valor):
		_destello_alfa = valor
		queue_redraw()


func _ready() -> void:
	custom_minimum_size = Vector2((RADIO_TAMBOR + RADIO_HUECO) * 2, (RADIO_TAMBOR + RADIO_HUECO) * 2)
	resized.connect(func() -> void: pivot_offset = size / 2.0)
	pivot_offset = size / 2.0
	set_process(false)


func _process(delta: float) -> void:
	_tiempo += delta
	queue_redraw()


## Resetea todos los huecos a "desconocido" para una partida nueva.
func preparar_partida(num_huecos: int) -> void:
	_num_huecos = num_huecos
	_estados.resize(num_huecos)
	_estados.fill(EstadoHueco.DESCONOCIDO)
	_huecos_destello.clear()
	_destello_alfa = 0.0
	_actualizar_latido()
	queue_redraw()


## Reemplaza el estado de todos los huecos a la vez (indexados 1..N, tal
## como los maneja el resto del juego). Espejo de dibujar_tambor() en
## terminal/ruleta.py: quien no aparece en `estados` se pinta como
## "desconocido".
func aplicar_estados(estados: Dictionary) -> void:
	for i in range(_num_huecos):
		_estados[i] = estados.get(i + 1, EstadoHueco.DESCONOCIDO)
	_actualizar_latido()
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


## Destello breve sobre unos huecos concretos (indexados 1..N). MainGame.gd
## lo usa cuando llega una pista dudosa: se ve de un vistazo a que huecos
## apunta, justo antes de que el jugador tenga que decidir si se la cree.
func destello(huecos: Array[int], duracion: float = 0.9) -> void:
	if huecos.is_empty():
		return
	_huecos_destello = huecos.duplicate()
	if efectos_reducidos:
		return
	var tween := create_tween()
	tween.tween_property(self, "_destello_alfa", 1.0, duracion * 0.2)
	tween.tween_property(self, "_destello_alfa", 0.0, duracion * 0.8)
	tween.tween_callback(func() -> void: _huecos_destello.clear())


func _draw() -> void:
	if _num_huecos <= 0:
		return

	var centro := size / 2.0
	_dibujar_chapa(centro)

	var font := get_theme_default_font()
	var font_size := 16

	for i in range(_num_huecos):
		var angulo := -PI / 2.0 + i * TAU / _num_huecos
		var pos := centro + Vector2(cos(angulo), sin(angulo)) * RADIO_TAMBOR
		var color := _color_de(_estados[i])

		# Sombra proyectada: da profundidad al hueco sobre la chapa.
		draw_circle(pos + Vector2(1.5, 2.5), RADIO_HUECO, COLOR_SOMBRA)
		draw_circle(pos, RADIO_HUECO, color)
		draw_arc(pos, RADIO_HUECO * 0.74, 0, TAU, 20, COLOR_BORDE * Color(1, 1, 1, 0.5), 2.0)
		draw_arc(pos, RADIO_HUECO, 0, TAU, 24, COLOR_BORDE, 2.0)

		if _estados[i] == EstadoHueco.CANDIDATO and not efectos_reducidos:
			_dibujar_latido(pos)
		if _huecos_destello.has(i + 1) and _destello_alfa > 0.0:
			var color_destello := COLOR_TENSION
			color_destello.a = _destello_alfa * 0.8
			draw_circle(pos, RADIO_HUECO + 5.0, color_destello)
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


## La placa del revolver sobre la que van los huecos: chapa oscura, dos
## aros de laton, remaches entre hueco y hueco y el eje en el centro.
func _dibujar_chapa(centro: Vector2) -> void:
	var radio_externo := RADIO_TAMBOR + RADIO_HUECO * 0.9
	draw_circle(centro, radio_externo, COLOR_CHAPA)
	draw_arc(centro, radio_externo, 0, TAU, 64, COLOR_ANILLO * Color(1, 1, 1, 0.7), 2.0)
	draw_arc(centro, RADIO_TAMBOR + RADIO_HUECO * 0.6, 0, TAU, 48, COLOR_ANILLO, 3.0)
	draw_arc(centro, RADIO_TAMBOR - RADIO_HUECO * 1.1, 0, TAU, 40, COLOR_ANILLO * Color(1, 1, 1, 0.45), 2.0)

	# Remaches: uno a mitad de camino entre cada par de huecos.
	for i in range(_num_huecos):
		var angulo := -PI / 2.0 + (i + 0.5) * TAU / _num_huecos
		var pos := centro + Vector2(cos(angulo), sin(angulo)) * radio_externo
		draw_circle(pos, 2.5, COLOR_ANILLO)

	# Eje.
	draw_circle(centro, RADIO_HUECO * 0.5, COLOR_CHAPA * Color(1.4, 1.4, 1.4, 1))
	draw_arc(centro, RADIO_HUECO * 0.5, 0, TAU, 20, COLOR_ANILLO, 2.0)


## Halo que respira alrededor de un hueco candidato: mientras las pistas lo
## señalen, el hueco "avisa" sin llegar a gritar.
func _dibujar_latido(pos: Vector2) -> void:
	var fase := 0.5 + 0.5 * sin(_tiempo * 3.4)
	var color := COLOR_CANDIDATO
	color.a = 0.15 + fase * 0.35
	draw_arc(pos, RADIO_HUECO + 3.0 + fase * 4.0, 0, TAU, 24, color, 2.0)


## Enciende el reloj del latido solo si hay algun candidato que lo necesite:
## sin candidatos (o con los efectos reducidos) el tambor no se repinta ni
## una vez por fotograma.
func _actualizar_latido() -> void:
	set_process(not efectos_reducidos and _estados.has(EstadoHueco.CANDIDATO))


func _color_de(estado_hueco: EstadoHueco) -> Color:
	if alto_contraste:
		return PALETA_CONTRASTE[estado_hueco]

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
