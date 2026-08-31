extends Control
class_name TamborView
## Vista del tambor: un cilindro de metal visto desde arriba en escorzo, con
## su canto, su chapa rayada, sus remaches y sus huecos, que gira sobre su
## eje al disparar y responde al raton.
##
## No conoce reglas del juego (bala, apuestas, dias...): solo pinta el
## estado que le pasa MainGame.gd via aplicar_estados(), espejo de
## calcular_estados()/dibujar_tambor() en terminal/ruleta.py, y avisa con
## `hueco_pulsado` de donde ha hecho clic el jugador. Quien decide que
## significa ese clic es MainGame.gd.
##
## Todo esta dibujado con `_draw()`, sin sprites ni modelo 3D: el tambor
## cambia de numero de huecos con la dificultad (6, 8 o 10), asi que una
## corona calculada siempre encaja, mientras que un sprite habria que
## tenerlo en tres versiones. El escorzo sale de aplastar el circulo en
## vertical (PERSPECTIVA) y de dibujarle un canto debajo: es un cilindro
## visto en angulo, no un disco plano.

## Avisa de que el jugador ha hecho clic en un hueco (numerado 1..N).
signal hueco_pulsado(numero: int)

const RADIO_TAMBOR := 116.0
const RADIO_HUECO := 21.0

## Cuanto se aplasta el circulo en vertical (1 = de frente, 0 = de canto) y
## cuanto asoma el canto del tambor por debajo.
const PERSPECTIVA := 0.58
const PROFUNDIDAD := 34.0

## Estados posibles de un hueco. Coinciden 1 a 1 con los cuatro que
## calcular_estados() usa en la version de terminal, mas DESCONOCIDO
## (huecos de los que aun no se sabe nada, sin equivalente ahi porque
## esa version simplemente no los marca).
enum EstadoHueco { DESCONOCIDO, PROBADO, CANDIDATO, SEGURO, PELIGRO }

## Color de cada estado, dentro de la paleta del juego: el hueco sin
## explorar es chapa en sombra, el ya probado es metal deslustrado, el
## candidato es bronce encendido, el declarado seguro es bronce firme y el
## peligroso es el unico rojo de la pantalla.
const COLORES := {
	EstadoHueco.DESCONOCIDO: Paleta.GRIS_PLOMO,
	EstadoHueco.PROBADO: Paleta.GRIS_CLARO,
	EstadoHueco.CANDIDATO: Paleta.BRONCE_VIVO,
	EstadoHueco.SEGURO: Paleta.BRONCE,
	EstadoHueco.PELIGRO: Paleta.ROJO,
}

## La misma paleta aclarada para el ajuste de alto contraste: los mismos
## cinco estados y el mismo significado, legibles sin depender de la
## penumbra (ver Ajustes.alto_contraste).
const ACLARADO_CONTRASTE := 0.45

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

## Angulo del tambor sobre su eje. Gira esto, y no `rotation` del nodo,
## porque el escorzo tiene que quedarse quieto: lo que rueda es el tambor
## dentro de su marco, no la camara alrededor.
var _giro := 0.0:
	set(valor):
		_giro = valor
		queue_redraw()

## Hueco (0-indexado) en tension: ya se disparo o marco pero el resultado
## aun no se ha revelado. -1 = ninguno. Igual con el que tiene el raton
## encima y con el que el jugador ha dejado elegido.
var _hueco_tension := -1
var _hueco_raton := -1
var _hueco_elegido := -1
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

## Posicion (0..1) del barrido de luz que recorre el tambor en el evento
## "clic metalico". Fuera de [0, 1] = no hay barrido.
var _barrido := -1.0:
	set(valor):
		_barrido = valor
		queue_redraw()

## Rayas de la chapa: angulo, radio y largo de cada una. Se sortean una vez
## al empezar la partida y se guardan, porque unas rayas que cambiasen en
## cada fotograma serian ruido, no textura.
var _rayas: Array[Vector3] = []

var _chispas: CPUParticles2D


## El tamaño minimo no es el de un circulo: el escorzo aplasta la altura a
## PERSPECTIVA y hay que sumarle el canto que asoma por debajo. Si se pidiera
## el cuadrado de siempre, el contenedor reservaria una franja vacia arriba y
## abajo que descolocaria el resto de la columna.
func _ready() -> void:
	custom_minimum_size = Vector2(
		(RADIO_TAMBOR + RADIO_HUECO) * 2,
		(RADIO_TAMBOR + RADIO_HUECO) * 2 * PERSPECTIVA + PROFUNDIDAD + RADIO_HUECO
	)
	resized.connect(func() -> void: pivot_offset = size / 2.0)
	pivot_offset = size / 2.0
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	set_process(false)
	_crear_chispas()


func _process(delta: float) -> void:
	_tiempo += delta
	queue_redraw()


# --- Lo que le pide MainGame --------------------------------------------------


## Resetea todos los huecos a "desconocido" para una partida nueva y sortea
## las rayas de la chapa.
func preparar_partida(num_huecos: int) -> void:
	_num_huecos = num_huecos
	_estados.resize(num_huecos)
	_estados.fill(EstadoHueco.DESCONOCIDO)
	_huecos_destello.clear()
	_destello_alfa = 0.0
	_hueco_elegido = -1
	_hueco_raton = -1
	_sortear_rayas()
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


## Deja un hueco marcado como elegido (o -1 para ninguno): se agranda y se
## queda fijo hasta que el jugador elija otro.
func elegir(numero: int) -> void:
	_hueco_elegido = numero - 1
	queue_redraw()


## Gira el tambor sobre su eje: coge carrerilla y frena en seco, como una
## rueda dentada que encuentra su trinquete.
##
## Da siempre un numero entero de vueltas, asi que cada hueco acaba donde
## empezo: el giro es dramatismo, no un sorteo. La bala se mueve por su
## patron (ver TamborJuicio), y eso no lo decide esta animacion.
func girar(duracion: float = 1.2) -> void:
	var vueltas := 2 + randi_range(0, 1)
	var tween := create_tween()
	# Casi todo el recorrido acelerando (EASE_IN) y un ultimo tramo corto
	# para el frenazo: si se frenara con una curva suave parecería que el
	# tambor se posa, y tiene que sonar a golpe.
	tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tween.tween_property(self, "_giro", _giro + TAU * vueltas, duracion * 0.82)
	tween.set_trans(Tween.TRANS_QUINT).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "_giro", _giro + TAU * (vueltas + 1), duracion * 0.18)
	await tween.finished


## Acerca la camara al tambor (en realidad lo agranda: es lo mismo con una
## sola vista) mientras dura la accion, y lo devuelve a su sitio.
func acercar(factor: float = 1.12, duracion: float = 0.35) -> void:
	if efectos_reducidos:
		return
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "scale", Vector2(factor, factor), duracion)


## Deshace acercar(). Se llama siempre, aunque el acercamiento no haya
## ocurrido (con los efectos reducidos no ocurre), porque tambien recoge la
## escala que deja pulsar().
func alejar(duracion: float = 0.45) -> void:
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(self, "scale", Vector2.ONE, duracion)


## Late en torno al hueco elegido antes de revelar un disparo o un
## farol: el resultado ya esta decidido, pero la vista retrasa el
## reveal un instante y pulsa un halo de bronce para meter tension.
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


## Pequeno pulso de escala para resaltar que el tambor acaba de
## cambiar (disparo o farol resueltos). Puramente decorativo.
func pulsar() -> void:
	var tween := create_tween()
	tween.tween_property(self, "scale", scale * 1.08, 0.08)
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


## Barrido de luz que cruza el tambor de lado a lado: el evento "clic
## metalico", que mueve la bala sola, se ve como un reflejo recorriendo la
## chapa.
func barrido(duracion: float = 0.5) -> void:
	if efectos_reducidos:
		return
	var tween := create_tween()
	tween.tween_property(self, "_barrido", 1.0, duracion).from(0.0)
	tween.tween_callback(func() -> void: _barrido = -1.0)


## Chispas rojas saliendo de un hueco: la bala.
func reventar(numero: int) -> void:
	if efectos_reducidos or _chispas == null:
		return
	_chispas.position = _posicion_de(numero - 1)
	_chispas.restart()


# --- Raton --------------------------------------------------------------------


## Raton sobre el tambor. Se usa _gui_input y no _input porque asi Godot ya
## filtra por nosotros: solo llegan los eventos que caen dentro de este
## Control, y en coordenadas locales, que es justo lo que necesita
## _hueco_en().
func _gui_input(evento: InputEvent) -> void:
	if evento is InputEventMouseMotion:
		var encima := _hueco_en(evento.position)
		if encima != _hueco_raton:
			_hueco_raton = encima
			queue_redraw()
	elif evento is InputEventMouseButton:
		var boton := evento as InputEventMouseButton
		if boton.pressed and boton.button_index == MOUSE_BUTTON_LEFT:
			var pulsado := _hueco_en(boton.position)
			if pulsado != -1:
				hueco_pulsado.emit(pulsado + 1)
				accept_event()


func _notification(que: int) -> void:
	# Al salir el raton del tambor no llega un MouseMotion mas, asi que sin
	# esto el ultimo hueco se quedaria iluminado para siempre.
	if que == NOTIFICATION_MOUSE_EXIT and _hueco_raton != -1:
		_hueco_raton = -1
		queue_redraw()


## Hueco (0-indexado) bajo el punto dado, o -1 si el punto no cae en ninguno.
## Se compara con el radio del hueco un poco crecido: apuntar a un circulo
## de 19 pixeles con el raton es incomodo si hay que clavarlo.
func _hueco_en(punto: Vector2) -> int:
	for i in range(_num_huecos):
		if punto.distance_to(_posicion_de(i)) <= RADIO_HUECO * 1.25:
			return i
	return -1


# --- Dibujo -------------------------------------------------------------------


## Pinta el tambor en tres pasadas, de lo que esta mas lejos a lo que esta
## mas cerca (el algoritmo del pintor): primero el canto, luego la chapa
## encima y por ultimo los huecos, que son lo que sobresale.
func _draw() -> void:
	if _num_huecos <= 0:
		return

	var centro := _centro()
	_dibujar_canto(centro)
	_dibujar_chapa(centro)

	# De atras hacia delante: los huecos de la mitad de abajo tapan a los de
	# arriba, que es lo que hace que se lea como un cilindro y no como un
	# dibujo plano.
	var orden := range(_num_huecos)
	orden.sort_custom(func(a: int, b: int) -> bool: return _posicion_de(a).y < _posicion_de(b).y)
	for i in orden:
		_dibujar_hueco(i)

	if _barrido >= 0.0:
		_dibujar_barrido(centro)


## Centro de la boca del tambor, que **no** es el centro del control: el
## canto cuelga por debajo, asi que la elipse se sube media profundidad para
## que el conjunto quede centrado a la vista.
func _centro() -> Vector2:
	return Vector2(size.x / 2.0, (size.y - PROFUNDIDAD) / 2.0)


## Posicion en pantalla del hueco `indice` (0-indexado), ya girada y
## aplastada por el escorzo.
func _posicion_de(indice: int) -> Vector2:
	var angulo := -PI / 2.0 + indice * TAU / _num_huecos + _giro
	return _centro() + Vector2(cos(angulo) * RADIO_TAMBOR, sin(angulo) * RADIO_TAMBOR * PERSPECTIVA)


## Radio con el que se pinta un hueco segun lo lejos que este: los de arriba
## (al fondo) algo mas pequenos que los de abajo (en primer plano).
func _radio_de(indice: int) -> float:
	var angulo := -PI / 2.0 + indice * TAU / _num_huecos + _giro
	return RADIO_HUECO * (0.88 + 0.12 * (sin(angulo) + 1.0) / 2.0)


## El canto del tambor: la banda de metal que asoma por debajo de la chapa,
## con estrias verticales para que se lea como una superficie curva.
func _dibujar_canto(centro: Vector2) -> void:
	var radio := RADIO_TAMBOR + RADIO_HUECO * 1.05
	var pasos := 32
	var arriba: Array[Vector2] = []
	for i in range(pasos + 1):
		var angulo := lerpf(0.0, PI, float(i) / pasos)
		arriba.append(centro + Vector2(cos(angulo) * radio, sin(angulo) * radio * PERSPECTIVA))

	var contorno := PackedVector2Array(arriba)
	for i in range(arriba.size() - 1, -1, -1):
		contorno.append(arriba[i] + Vector2(0, PROFUNDIDAD))
	draw_colored_polygon(contorno, _color(Paleta.NEGRO.lerp(Paleta.GRIS_PLOMO, 0.55)))

	for i in range(1, arriba.size() - 1, 2):
		var estria := _color(Paleta.NEGRO)
		estria.a = 0.5
		draw_line(arriba[i], arriba[i] + Vector2(0, PROFUNDIDAD), estria, 1.0)
	draw_polyline(PackedVector2Array(arriba), _color(Paleta.BRONCE), 2.0)


## La chapa sobre la que van los huecos: disco en escorzo, rayado de uso,
## dos aros de bronce, remaches y el eje.
func _dibujar_chapa(centro: Vector2) -> void:
	var radio := RADIO_TAMBOR + RADIO_HUECO * 1.05

	# Con la transformada aplastada, todo lo que se dibuje en circulo sale
	# en elipse; se restaura despues para que los numeros no salgan chatos.
	draw_set_transform(centro, 0.0, Vector2(1.0, PERSPECTIVA))
	draw_circle(Vector2.ZERO, radio, _color(Paleta.GRIS_PLOMO))
	draw_arc(Vector2.ZERO, radio, 0, TAU, 64, _color(Paleta.BRONCE), 2.5)
	draw_arc(Vector2.ZERO, RADIO_TAMBOR - RADIO_HUECO * 1.2, 0, TAU, 48,
		_color(Paleta.BRONCE_APAGADO), 1.5)

	# Rayas de uso, giradas con el tambor.
	for raya in _rayas:
		var angulo: float = raya.x + _giro
		var direccion := Vector2(cos(angulo), sin(angulo))
		var raya_color := _color(Paleta.BRONCE_APAGADO)
		raya_color.a = 0.22
		draw_line(direccion * raya.y, direccion * (raya.y + raya.z), raya_color, 1.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# Remaches: uno entre cada par de huecos, en su sitio de la elipse.
	for i in range(_num_huecos):
		var angulo := -PI / 2.0 + (i + 0.5) * TAU / _num_huecos + _giro
		var pos := centro + Vector2(
			cos(angulo) * radio * 0.94, sin(angulo) * radio * 0.94 * PERSPECTIVA
		)
		draw_circle(pos, 2.5, _color(Paleta.BRONCE))

	# Eje.
	draw_set_transform(centro, 0.0, Vector2(1.0, PERSPECTIVA))
	draw_circle(Vector2.ZERO, RADIO_HUECO * 0.62, _color(Paleta.NEGRO))
	draw_arc(Vector2.ZERO, RADIO_HUECO * 0.62, 0, TAU, 24, _color(Paleta.BRONCE), 2.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


## Un hueco, con todo lo que puede llevar encima superpuesto en orden: la
## boca, el latido si es candidato, el aspa si ya se probo, el destello de
## una pista dudosa, el borde del raton, el del hueco elegido, el halo de
## tension y el numero.
##
## El orden importa: lo que se dibuja despues tapa a lo anterior, y de ahi
## que el numero vaya el ultimo (tiene que leerse siempre) y el halo de
## tension penultimo (es lo que el jugador esta mirando en ese momento).
func _dibujar_hueco(indice: int) -> void:
	var pos := _posicion_de(indice)
	var radio := _radio_de(indice)
	var estado := _estados[indice]
	var color := _color(COLORES[estado])

	# Boca del hueco: sombra proyectada, fondo y un anillo interior que
	# insinua la profundidad del cilindro.
	var sombra := _color(Paleta.NEGRO)
	sombra.a = 0.55
	draw_circle(pos + Vector2(1.5, 2.5), radio, sombra)
	draw_circle(pos, radio, color)
	var interior := _color(Paleta.NEGRO)
	interior.a = 0.45
	draw_arc(pos, radio * 0.72, 0, TAU, 20, interior, 2.0)
	draw_arc(pos, radio, 0, TAU, 24, _color(Paleta.NEGRO), 2.0)

	if estado == EstadoHueco.CANDIDATO and not efectos_reducidos:
		_dibujar_latido(pos, radio)
	if estado == EstadoHueco.PROBADO:
		_dibujar_aspa(pos, radio)
	if _huecos_destello.has(indice + 1) and _destello_alfa > 0.0:
		var destello_color := _color(Paleta.BRONCE_VIVO)
		destello_color.a = _destello_alfa * 0.8
		draw_circle(pos, radio + 5.0, destello_color)
	if indice == _hueco_raton:
		var brillo := _color(Paleta.BRONCE_VIVO)
		brillo.a = 0.75
		draw_arc(pos, radio + 3.0, 0, TAU, 24, brillo, 2.0)
	if indice == _hueco_elegido:
		draw_arc(pos, radio + 5.0, 0, TAU, 28, _color(Paleta.BRONCE_VIVO), 3.0)
	if indice == _hueco_tension:
		var halo := _color(Paleta.BRONCE_VIVO)
		halo.a = 0.35 + _pulso_tension * 0.65
		draw_arc(pos, radio + 4.0 + _pulso_tension * 8.0, 0, TAU, 24, halo, 3.0)

	_dibujar_numero(indice, pos)


## El numero del hueco, en negro sobre los rellenos claros (bronce y rojo) y
## en bronce claro sobre los oscuros: es el mismo criterio que se sigue al
## elegir el color de un texto sobre un fondo, y lo que evita tener que
## mirar dos veces para leer un "8".
##
## Crece un par de puntos cuando el hueco esta señalado con el raton o
## elegido, que es la unica pista de tamaño que da la vista.
func _dibujar_numero(indice: int, pos: Vector2) -> void:
	var font := get_theme_default_font()
	var font_size := 16
	if indice == _hueco_elegido or indice == _hueco_raton:
		font_size = 18
	var texto := str(indice + 1)
	var medida := font.get_string_size(texto, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size)
	# El numero se lee mejor en negro sobre los huecos claros (bronce, rojo)
	# y en bronce claro sobre los oscuros.
	var color_texto := _color(Paleta.BRONCE_CLARO)
	if _estados[indice] in [EstadoHueco.CANDIDATO, EstadoHueco.SEGURO, EstadoHueco.PELIGRO]:
		color_texto = _color(Paleta.NEGRO)
	draw_string(
		font, pos - medida / 2.0 + Vector2(0, medida.y * 0.35),
		texto, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size, color_texto
	)


## Halo que respira alrededor de un hueco candidato: mientras las pistas lo
## señalen, el hueco "avisa" sin llegar a gritar.
func _dibujar_latido(pos: Vector2, radio: float) -> void:
	var fase := 0.5 + 0.5 * sin(_tiempo * 3.4)
	var color := _color(Paleta.BRONCE_VIVO)
	color.a = 0.15 + fase * 0.35
	draw_arc(pos, radio + 3.0 + fase * 4.0, 0, TAU, 24, color, 2.0)


## Aspa sobre un hueco ya disparado: ademas del gris, una marca que se lee
## igual aunque el jugador no distinga los tonos.
func _dibujar_aspa(pos: Vector2, radio: float) -> void:
	var brazo := radio * 0.45
	var color := _color(Paleta.NEGRO)
	color.a = 0.75
	draw_line(pos + Vector2(-brazo, -brazo), pos + Vector2(brazo, brazo), color, 2.5)
	draw_line(pos + Vector2(-brazo, brazo), pos + Vector2(brazo, -brazo), color, 2.5)


## Reflejo que cruza la chapa de izquierda a derecha.
func _dibujar_barrido(centro: Vector2) -> void:
	var radio := RADIO_TAMBOR + RADIO_HUECO * 1.05
	var x := centro.x + lerpf(-radio, radio, _barrido)
	var alto := radio * PERSPECTIVA
	var color := _color(Paleta.BRONCE_CLARO)
	# Se apaga en los extremos del recorrido para que entre y salga.
	color.a = 0.5 * sin(PI * _barrido)
	draw_line(Vector2(x, centro.y - alto), Vector2(x, centro.y + alto + PROFUNDIDAD), color, 6.0)


# --- Auxiliares ----------------------------------------------------------------


## Devuelve el color tal cual, o aclarado si el jugador pidio alto contraste.
func _color(color: Color) -> Color:
	return Paleta.aclarar(color, ACLARADO_CONTRASTE) if alto_contraste else color


## Destino de tween_method() en tension(). Hace falta un metodo, y no un
## tween_property sobre la variable, porque cada paso tiene que repintar.
func _set_pulso_tension(valor: float) -> void:
	_pulso_tension = valor
	queue_redraw()


## Sortea las rayas de uso de la chapa una vez por partida y las guarda
## (angulo, radio y largo de cada una).
##
## Se sortean y se guardan, en vez de calcularse en _draw(), porque unas
## rayas distintas en cada fotograma no serian textura: serian ruido
## parpadeando. Al ir en coordenadas polares giran con el tambor solas.
func _sortear_rayas() -> void:
	_rayas.clear()
	for _i in range(22):
		var angulo := randf() * TAU
		var radio := randf_range(RADIO_HUECO, RADIO_TAMBOR - RADIO_HUECO * 1.3)
		_rayas.append(Vector3(angulo, radio, randf_range(6.0, 26.0)))


## Enciende el reloj del latido solo si hay algun candidato que lo necesite:
## sin candidatos (o con los efectos reducidos) el tambor no se repinta ni
## una vez por fotograma.
func _actualizar_latido() -> void:
	set_process(not efectos_reducidos and _estados.has(EstadoHueco.CANDIDATO))


## Surtidor de chispas para el impacto. Se crea por codigo (y no en la
## escena) porque es parte de como se pinta el tambor, igual que el resto
## de este archivo: la escena solo pone el nodo del tambor.
func _crear_chispas() -> void:
	_chispas = CPUParticles2D.new()
	_chispas.emitting = false
	_chispas.one_shot = true
	_chispas.explosiveness = 0.95
	_chispas.amount = 48
	_chispas.lifetime = 0.7
	_chispas.direction = Vector2(0, -1)
	_chispas.spread = 180.0
	_chispas.gravity = Vector2(0, 420)
	_chispas.initial_velocity_min = 90.0
	_chispas.initial_velocity_max = 260.0
	_chispas.scale_amount_min = 1.0
	_chispas.scale_amount_max = 2.5
	_chispas.color = Paleta.ROJO
	add_child(_chispas)
