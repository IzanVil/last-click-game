extends Control
class_name Icono
## Iconos del HUD, dibujados con `_draw()`: calendario (dias), moneda
## (puntos), lupa (pistas) y escudo (marcas de farol).
##
## Son cuatro formas geometricas de cuatro trazos cada una, no un tipo de
## letra de iconos ni un atlas de sprites: al dibujarlos se ajustan solos al
## cuerpo de letra (ver "texto grande") y al color de la paleta, y no hay un
## archivo mas que licenciar. Ver assets/README.md.

enum Tipo { CALENDARIO, MONEDA, LUPA, ESCUDO }

@export var tipo: Tipo = Tipo.CALENDARIO:
	set(valor):
		tipo = valor
		queue_redraw()

@export var color: Color = Paleta.BRONCE:
	set(valor):
		color = valor
		queue_redraw()

## Lado del icono. Lo fija MainGame junto al cuerpo de letra del HUD para
## que icono y numero crezcan a la vez.
@export var lado: float = 18.0:
	set(valor):
		lado = valor
		custom_minimum_size = Vector2(lado, lado)
		queue_redraw()


## El icono no captura el raton: es un dibujo dentro de una fila de datos,
## y comerse los clics ahi solo serviria para tapar lo que haya detras.
func _ready() -> void:
	custom_minimum_size = Vector2(lado, lado)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Cada icono se dibuja dentro de un cuadrado de lado `lado`, centrado en el
## espacio que le den y con el trazo proporcional a ese lado: asi los cuatro
## pesan lo mismo en la barra y siguen cuadrando cuando "texto grande" los
## agranda.
func _draw() -> void:
	var caja := Rect2((size - Vector2(lado, lado)) / 2.0, Vector2(lado, lado))
	var grosor := maxf(1.0, lado * 0.09)
	match tipo:
		Tipo.CALENDARIO:
			_dibujar_calendario(caja, grosor)
		Tipo.MONEDA:
			_dibujar_moneda(caja, grosor)
		Tipo.LUPA:
			_dibujar_lupa(caja, grosor)
		Tipo.ESCUDO:
			_dibujar_escudo(caja, grosor)


## Hoja de calendario: marco, la barra del encabezado y las dos anillas.
func _dibujar_calendario(caja: Rect2, grosor: float) -> void:
	var hoja := Rect2(
		caja.position + Vector2(0, caja.size.y * 0.18),
		Vector2(caja.size.x, caja.size.y * 0.82)
	)
	draw_rect(hoja, color, false, grosor)
	var barra := Rect2(hoja.position, Vector2(hoja.size.x, hoja.size.y * 0.28))
	draw_rect(barra, color, true)
	for x in [0.3, 0.7]:
		var pin := caja.position + Vector2(caja.size.x * x, 0)
		draw_line(pin, pin + Vector2(0, caja.size.y * 0.22), color, grosor)


## Moneda: dos circunferencias concentricas y un canto marcado.
func _dibujar_moneda(caja: Rect2, grosor: float) -> void:
	var centro := caja.get_center()
	var radio := caja.size.x * 0.46
	draw_arc(centro, radio, 0, TAU, 24, color, grosor)
	draw_arc(centro, radio * 0.55, 0, TAU, 20, color, grosor * 0.8)
	draw_line(centro + Vector2(0, -radio * 0.3), centro + Vector2(0, radio * 0.3), color, grosor)


## Lupa: la lente y el mango en diagonal.
func _dibujar_lupa(caja: Rect2, grosor: float) -> void:
	var centro := caja.get_center() - caja.size * 0.12
	var radio := caja.size.x * 0.34
	draw_arc(centro, radio, 0, TAU, 24, color, grosor)
	var mango := centro + Vector2(1, 1).normalized() * radio
	draw_line(mango, mango + Vector2(1, 1).normalized() * caja.size.x * 0.34, color, grosor * 1.4)


## Escudo: los hombros rectos y la punta abajo.
func _dibujar_escudo(caja: Rect2, grosor: float) -> void:
	var ancho := caja.size.x
	var alto := caja.size.y
	var puntos := PackedVector2Array([
		caja.position + Vector2(ancho * 0.08, alto * 0.12),
		caja.position + Vector2(ancho * 0.92, alto * 0.12),
		caja.position + Vector2(ancho * 0.92, alto * 0.55),
		caja.position + Vector2(ancho * 0.5, alto * 0.95),
		caja.position + Vector2(ancho * 0.08, alto * 0.55),
	])
	# El poligono se cierra repitiendo el primer punto: draw_polyline no lo
	# hace solo, y un escudo abierto por arriba se ve raro.
	puntos.append(puntos[0])
	draw_polyline(puntos, color, grosor)
