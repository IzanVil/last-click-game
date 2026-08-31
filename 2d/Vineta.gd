extends Control
class_name Vineta
## Capa que se dibuja por encima de toda la interfaz: la viñeta que oscurece
## los bordes, los resplandores de color de los eventos y el cierre en iris
## con el que termina una partida.
##
## Va por encima de `Centro` en la escena (el orden de hermanos manda al
## dibujar) y no captura el raton, asi que los botones de debajo se siguen
## pulsando con normalidad.
##
## Como FondoTaller, es decorado puro: recibe ordenes de MainGame.gd y no
## sabe nada de balas, dias ni apuestas.

const COLOR_VINETA := Color(0, 0, 0, 1)  # negro puro, mas oscuro que el fondo

## Cuanto se oscurecen los bordes en reposo.
const INTENSIDAD_BASE := 0.55

## Opacidad maxima de un resplandor de evento. Bastante menos que la viñeta
## porque el resplandor tiñe de color: pasado de ahi deja de ser un aviso en
## los bordes y se come la partida.
const INTENSIDAD_RESPLANDOR := 0.32

var efectos_reducidos := false

var _vineta: GradientTexture2D
var _halo: GradientTexture2D
var _resplandor_color := Color(1, 1, 1, 0)
var _resplandor_alfa := 0.0:
	set(valor):
		_resplandor_alfa = valor
		queue_redraw()

## Radio del hueco por el que aun se ve la pantalla, en fraccion de la
## diagonal: 1 = abierto del todo, 0 = a oscuras. Ver cerrar()/abrir().
var _apertura := 1.0:
	set(valor):
		_apertura = valor
		queue_redraw()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_vineta = _crear_degradado(0.55, 0.18)
	# El resplandor se ciñe mucho mas al borde que la viñeta: asi la zona
	# donde se juega (el centro) no se tiñe entera de rojo.
	_halo = _crear_degradado(0.75, 0.04)


## Tiñe los bordes de la pantalla con un color que entra y se va: rojo para
## el tambor caliente, ambar para una pista dudosa... Quien llama elige el
## color; aqui solo se pinta.
func resplandor(color: Color, duracion: float = 1.4) -> void:
	_resplandor_color = color
	if efectos_reducidos:
		return
	var tween := create_tween()
	tween.tween_property(self, "_resplandor_alfa", INTENSIDAD_RESPLANDOR, duracion * 0.25)
	tween.tween_property(self, "_resplandor_alfa", 0.0, duracion * 0.75)


## Cierra la pantalla en iris, como el final de una pelicula muda. Se espera
## (await) para encadenar lo que venga despues, normalmente volver al menu.
func cerrar(duracion: float = 0.6) -> void:
	if efectos_reducidos:
		_apertura = 0.0
		return
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tween.tween_property(self, "_apertura", 0.0, duracion)
	await tween.finished


## Vuelve a abrir el iris. No hace falta esperarlo: la pantalla de debajo ya
## esta puesta y se va descubriendo mientras el jugador la mira.
func abrir(duracion: float = 0.6) -> void:
	if efectos_reducidos:
		_apertura = 1.0
		return
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "_apertura", 1.0, duracion)


## Tres capas, siempre en el mismo orden: la viñeta de reposo, el resplandor
## de color del evento que toque y, si la partida ha terminado, el iris
## cerrandose. Van de la mas permanente a la mas puntual, porque cada una
## tiene que poder tapar a la anterior.
func _draw() -> void:
	if size.x <= 0.0 or size.y <= 0.0:
		return

	var rect := Rect2(Vector2.ZERO, size)
	var base := COLOR_VINETA
	base.a = INTENSIDAD_BASE
	draw_texture_rect(_vineta, rect, false, base)

	if _resplandor_alfa > 0.0:
		var color := _resplandor_color
		color.a = _resplandor_alfa
		draw_texture_rect(_halo, rect, false, color)

	if _apertura < 1.0:
		_dibujar_iris()


## El iris es un anillo negro que se cierra hacia el centro: un unico arco
## de trazo muy grueso (la mitad de la diagonal, suficiente para tapar las
## esquinas) cuyo radio va menguando. La viñeta dibujada encima le suaviza
## el borde.
func _dibujar_iris() -> void:
	var centro := size / 2.0
	var diagonal := size.length()
	var radio := _apertura * diagonal / 2.0
	draw_arc(centro, radio + diagonal / 2.0, 0, TAU, 64, COLOR_VINETA, diagonal, true)


## Degradado radial: nada en el centro y opaco en los bordes (al reves que
## la luz de FondoTaller). `codo` y `opacidad_codo` deciden como de rapido
## se cierra sobre el borde, que es lo unico que distingue la viñeta de
## fondo del resplandor de los eventos.
func _crear_degradado(codo: float, opacidad_codo: float) -> GradientTexture2D:
	var degradado := Gradient.new()
	degradado.offsets = PackedFloat32Array([0.0, codo, 1.0])
	degradado.colors = PackedColorArray([
		Color(1, 1, 1, 0), Color(1, 1, 1, opacidad_codo), Color(1, 1, 1, 1),
	])

	var textura := GradientTexture2D.new()
	textura.gradient = degradado
	textura.fill = GradientTexture2D.FILL_RADIAL
	textura.fill_from = Vector2(0.5, 0.5)
	textura.fill_to = Vector2(1.0, 0.5)
	textura.width = 256
	textura.height = 256
	return textura
