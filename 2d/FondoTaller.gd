extends Control
class_name FondoTaller
## Fondo del taller: engranajes girando en penumbra y una luz calida sobre
## el tambor, dibujados a mano con `_draw()`.
##
## Es solo decorado: no conoce reglas ni estado de la partida. MainGame.gd
## le pide "calentarse" cuando ocurre el evento `tambor_caliente`, y eso
## unicamente cambia como parpadea la luz.
##
## Todo se dibuja por codigo, sin texturas ni sprites, por el mismo motivo
## que los sonidos se sintetizan en `assets/audio/synth_sfx.py`: no meter
## assets de terceros ni licencias que gestionar en un juego que cabe en
## un puñado de archivos de texto. Los engranajes van a distinta
## profundidad (los grandes al fondo, mas oscuros y lentos; los pequeños
## delante) para dar la sensacion de maquina viva que un ParallaxBackground
## daria con sprites.

## Engranajes del fondo: posicion relativa al tamaño de la ventana (0..1),
## radio relativo al lado menor, dientes, y vueltas por minuto (con signo:
## los engranajes que engranan entre si giran al reves uno del otro).
const ENGRANAJES: Array[Dictionary] = [
	{"ancla": Vector2(0.12, 0.18), "radio": 0.34, "dientes": 18, "rpm": 0.9, "tono": 0.55},
	{"ancla": Vector2(0.88, 0.30), "radio": 0.26, "dientes": 14, "rpm": -1.3, "tono": 0.75},
	{"ancla": Vector2(0.78, 0.86), "radio": 0.38, "dientes": 20, "rpm": 0.7, "tono": 0.45},
	{"ancla": Vector2(0.20, 0.92), "radio": 0.20, "dientes": 12, "rpm": -1.8, "tono": 0.9},
	{"ancla": Vector2(0.50, 0.06), "radio": 0.14, "dientes": 10, "rpm": 2.2, "tono": 1.0},
]

const COLOR_METAL := Color(0.32, 0.26, 0.17, 1)
const COLOR_LUZ := Color(0.85, 0.60, 0.28, 1)
const COLOR_LUZ_CALIENTE := Color(0.95, 0.25, 0.10, 1)

## Cuanto se ve el metal sobre el fondo. Muy poco a proposito: los
## engranajes deben insinuarse en la penumbra, no competir con el tambor.
const ALFA_METAL := 0.13
const ALFA_LUZ := 0.16

## Lo que tarda el "calor" del tambor en enfriarse del todo.
const ENFRIAMIENTO := 4.0

## Con los efectos reducidos los engranajes se quedan quietos y la luz deja
## de parpadear: ni un repintado por fotograma (ver Ajustes.efectos_reducidos).
var efectos_reducidos := false:
	set(valor):
		efectos_reducidos = valor
		set_process(not valor)
		queue_redraw()

var _tiempo := 0.0
## 0 = tambor frio, 1 = recien calentado. Solo tiñe y agita la luz.
var _calor := 0.0
var _luz: GradientTexture2D


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_luz = _crear_luz()


func _process(delta: float) -> void:
	_tiempo += delta
	queue_redraw()


## Enciende el resplandor rojizo del tambor caliente, que se apaga solo.
func calentar() -> void:
	_calor = 1.0
	queue_redraw()
	if efectos_reducidos:
		return
	var tween := create_tween()
	tween.tween_property(self, "_calor", 0.0, ENFRIAMIENTO)


func _draw() -> void:
	if size.x <= 0.0 or size.y <= 0.0:
		return
	_dibujar_luz()
	var lado := minf(size.x, size.y)
	for engranaje in ENGRANAJES:
		var ancla: Vector2 = engranaje["ancla"]
		var radio_relativo: float = engranaje["radio"]
		var rpm: float = engranaje["rpm"]
		var dientes: int = engranaje["dientes"]
		var tono: float = engranaje["tono"]
		_dibujar_engranaje(ancla * size, radio_relativo * lado, dientes, _tiempo * rpm * TAU / 60.0, tono)


## Luz calida sobre el centro de la pantalla (donde esta el tambor), con un
## parpadeo lento de lampara de gas que se vuelve nervioso y rojizo mientras
## el tambor esta caliente.
func _dibujar_luz() -> void:
	# Las dos frecuencias son deliberadamente bajas (por debajo de 2 Hz): un
	# parpadeo rapido sobre toda la pantalla es justo lo que hay que evitar
	# por fotosensibilidad, y para "lampara de gas nerviosa" basta con esto.
	var parpadeo := 0.0
	if not efectos_reducidos:
		parpadeo = 0.06 * sin(_tiempo * 2.3) + _calor * 0.10 * sin(_tiempo * 9.5)
	var color := COLOR_LUZ.lerp(COLOR_LUZ_CALIENTE, _calor)
	color.a = maxf(0.0, ALFA_LUZ + _calor * 0.10 + parpadeo)
	draw_texture_rect(_luz, Rect2(Vector2.ZERO, size), false, color)


func _dibujar_engranaje(
	centro: Vector2, radio: float, dientes: int, giro: float, tono: float
) -> void:
	var color := COLOR_METAL * tono
	color.a = ALFA_METAL
	var color_hueco := color
	color_hueco.a = ALFA_METAL * 0.6

	# Cuerpo, dientes y eje. Los dientes son segmentos gruesos que asoman
	# del cuerpo: a esta opacidad se leen igual que un poligono dentado y
	# cuestan una fraccion de los vertices.
	draw_circle(centro, radio * 0.82, color)
	var largo := radio * 0.22
	var grosor := radio * TAU / (dientes * 2.4)
	for i in range(dientes):
		var angulo := giro + i * TAU / dientes
		var direccion := Vector2(cos(angulo), sin(angulo))
		draw_line(centro + direccion * (radio * 0.78), centro + direccion * (radio * 0.78 + largo),
			color, grosor)

	# Radios y buje: sin ellos la rueda gira sin que se note que gira.
	for i in range(6):
		var angulo := giro + i * TAU / 6.0
		var direccion := Vector2(cos(angulo), sin(angulo))
		draw_line(centro + direccion * (radio * 0.22), centro + direccion * (radio * 0.74),
			color_hueco, radio * 0.05)
	draw_arc(centro, radio * 0.20, 0, TAU, 24, color_hueco, radio * 0.06)


## Degradado radial (transparente en el centro, nada en los bordes) que se
## estira a toda la pantalla. Se crea una sola vez: repintarlo por
## fotograma seria regenerar la textura entera cada vez.
func _crear_luz() -> GradientTexture2D:
	var degradado := Gradient.new()
	degradado.offsets = PackedFloat32Array([0.0, 0.45, 1.0])
	degradado.colors = PackedColorArray([
		Color(1, 1, 1, 1), Color(1, 1, 1, 0.35), Color(1, 1, 1, 0),
	])

	var textura := GradientTexture2D.new()
	textura.gradient = degradado
	textura.fill = GradientTexture2D.FILL_RADIAL
	textura.fill_from = Vector2(0.5, 0.5)
	textura.fill_to = Vector2(1.0, 0.5)
	textura.width = 256
	textura.height = 256
	return textura
