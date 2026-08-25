extends Control
class_name TamborView
## Vista del tambor de la ruleta: dibuja los huecos en corona y anima el
## giro y el revelado de un disparo. No conoce reglas del juego (rondas,
## balas, condicion de victoria): solo pinta los estados que le pasa
## MainGame.gd via preparar_ronda()/revelar().

const RADIO_TAMBOR := 90.0
const RADIO_HUECO := 18.0

const COLOR_HUECO_OCULTO := Color(0.35, 0.35, 0.4, 1)
const COLOR_HUECO_BALA := Color(0.85, 0.15, 0.15, 1)
const COLOR_HUECO_VACIO := Color(0.2, 0.75, 0.35, 1)
const COLOR_BORDE := Color(0.05, 0.05, 0.08, 1)
const COLOR_TEXTO := Color(0.95, 0.95, 0.95, 1)
const COLOR_ANILLO := Color(0.5, 0.45, 0.15, 1)

enum EstadoHueco { OCULTO, VACIO, BALA }

var _num_huecos := 10
var _estados: Array[int] = []


func _ready() -> void:
	custom_minimum_size = Vector2((RADIO_TAMBOR + RADIO_HUECO) * 2, (RADIO_TAMBOR + RADIO_HUECO) * 2)
	resized.connect(func(): pivot_offset = size / 2.0)
	pivot_offset = size / 2.0


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
	var vueltas := 2 + randi_range(0, 2)
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "rotation", rotation + TAU * vueltas, duracion)
	await tween.finished


## Marca el hueco `numero` (1-indexado, como lo escribe el jugador) como
## bala o vacio, y lo resalta con un pequeno "pulso" de escala.
func revelar(numero: int, es_bala: bool) -> void:
	var indice := numero - 1
	if indice < 0 or indice >= _estados.size():
		return
	_estados[indice] = EstadoHueco.BALA if es_bala else EstadoHueco.VACIO
	queue_redraw()

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
		var color := COLOR_HUECO_OCULTO
		match _estados[i]:
			EstadoHueco.BALA:
				color = COLOR_HUECO_BALA
			EstadoHueco.VACIO:
				color = COLOR_HUECO_VACIO

		draw_circle(pos, RADIO_HUECO, color)
		draw_arc(pos, RADIO_HUECO, 0, TAU, 24, COLOR_BORDE, 2.0)

		var texto := str(i + 1)
		var text_size := font.get_string_size(texto, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size)
		draw_string(
			font, pos - text_size / 2.0 + Vector2(0, text_size.y * 0.35),
			texto, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size, COLOR_TEXTO
		)
