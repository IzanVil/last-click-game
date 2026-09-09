extends SceneTree
## Tests de la geometria pulsable de TamborView.gd.
##
##     godot --headless --script res://tests/test_tambor_view.gd --path 2d
##
## Lo que importa aqui es que hueco_en() y centro_hueco() no se separen:
## centro_hueco() es la que usa _draw() para pintar, asi que si el
## hit-testing se desalineara del dibujo, pulsar un hueco dispararia a
## otro sin que nada fallase de forma visible. Por eso casi todo son
## comprobaciones de ida y vuelta contra la posicion dibujada.
##
## El nodo no se mete en el arbol: hueco_en()/centro_hueco() solo
## dependen de `size` y de las constantes, asi que basta con darle un
## tamano a mano y ahorrarse levantar la escena.

const Harness := preload("res://tests/harness.gd")
const TamborViewScript := preload("res://TamborView.gd")

## El mismo tamano que se fija en _ready() via custom_minimum_size.
const LADO := (TamborViewScript.RADIO_TAMBOR + TamborViewScript.RADIO_HUECO) * 2.0

var _h := Harness.new()

## TamborView es un Node: fuera del arbol nadie lo libera, y dejarlos
## sueltos hace que Godot avise de RIDs y objetos filtrados al salir (un
## "ERROR: resources still in use" que ensuciaria el log de la CI y
## podria tapar uno de verdad). Se apuntan aqui y se liberan al final.
var _creados: Array[Node] = []


func _init() -> void:
	var nombres: Array[String] = []
	for metodo in get_method_list():
		if metodo.name.begins_with("_test_"):
			nombres.append(metodo.name)
	nombres.sort()

	print("Ejecutando %d tests de TamborView...\n" % nombres.size())
	for nombre in nombres:
		call(nombre)

	var codigo := _h.resumen(nombres.size())
	for nodo in _creados:
		nodo.free()
	_creados.clear()
	quit(codigo)


# --- Utilidades de test ------------------------------------------------


## Un tambor listo para preguntarle por su geometria, fuera del arbol.
func _tambor(num_huecos := 10) -> TamborView:
	var tambor: TamborView = TamborViewScript.new()
	tambor.size = Vector2(LADO, LADO)
	tambor.preparar_ronda(num_huecos)
	_creados.append(tambor)
	return tambor


# --- Geometria pulsable -------------------------------------------------


func _test_el_centro_de_cada_hueco_devuelve_ese_hueco() -> void:
	# La comprobacion clave: lo que se dibuja es lo que se pulsa.
	for num_huecos in [6, 10, 12]:
		var tambor := _tambor(num_huecos)
		for indice in range(num_huecos):
			_h.igual(
				tambor.hueco_en(tambor.centro_hueco(indice)),
				indice + 1,
				(
					"tambor de %d: el centro dibujado del hueco %d se pulsa como %d"
					% [num_huecos, indice + 1, indice + 1]
				)
			)


func _test_el_eje_del_tambor_no_es_de_nadie() -> void:
	var tambor := _tambor()
	_h.igual(tambor.hueco_en(tambor.size / 2.0), -1, "el centro del tambor no es pulsable")


func _test_fuera_del_tambor_no_hay_hueco() -> void:
	var tambor := _tambor()
	_h.igual(tambor.hueco_en(Vector2.ZERO), -1, "la esquina superior izquierda no es pulsable")
	_h.igual(tambor.hueco_en(Vector2(LADO * 4, LADO * 4)), -1, "muy lejos del tambor no hay hueco")


func _test_el_borde_del_hueco_delimita_lo_pulsable() -> void:
	var tambor := _tambor()
	var centro := tambor.centro_hueco(0)
	var radio := TamborViewScript.RADIO_HUECO
	_h.igual(tambor.hueco_en(centro + Vector2(radio - 1.0, 0)), 1, "justo dentro del borde: pulsa")
	_h.igual(
		tambor.hueco_en(centro + Vector2(radio + 1.0, 0)), -1, "justo fuera del borde: no pulsa"
	)


func _test_los_huecos_no_se_solapan() -> void:
	# Si dos huecos se tocaran, hueco_en() devolveria siempre el de menor
	# indice para la zona comun y habria numeros imposibles de pulsar.
	for num_huecos in [6, 10, 12]:
		var tambor := _tambor(num_huecos)
		var separacion := tambor.centro_hueco(0).distance_to(tambor.centro_hueco(1))
		_h.ok(
			separacion > TamborViewScript.RADIO_HUECO * 2.0,
			(
				"tambor de %d: huecos contiguos separados (%.1f > %.1f)"
				% [num_huecos, separacion, TamborViewScript.RADIO_HUECO * 2.0]
			)
		)


func _test_todos_los_huecos_caben_en_el_rectangulo() -> void:
	# Si un hueco se saliera del Control, sus clicks nunca llegarian a
	# _gui_input y ese numero solo se podria jugar escribiendolo.
	var tambor := _tambor()
	var radio := TamborViewScript.RADIO_HUECO
	for indice in range(10):
		var centro := tambor.centro_hueco(indice)
		var dentro := (
			centro.x - radio >= 0.0
			and centro.y - radio >= 0.0
			and centro.x + radio <= LADO
			and centro.y + radio <= LADO
		)
		_h.ok(dentro, "el hueco %d cabe entero en el rectangulo del nodo" % [indice + 1])


func _test_el_hueco_1_esta_arriba() -> void:
	# Convenio de dibujo: se empieza en -PI/2 y se va en sentido horario.
	# Si esto cambiase, el tambor seguiria siendo jugable pero los
	# numeros bailarian respecto a lo que espera el jugador.
	var tambor := _tambor()
	var centro := tambor.centro_hueco(0)
	_h.cerca(centro.x, LADO / 2.0, "el hueco 1 esta centrado en horizontal")
	_h.ok(centro.y < LADO / 2.0, "el hueco 1 esta en la mitad de arriba")


# --- Estados revelados --------------------------------------------------


func _test_una_ronda_nueva_empieza_toda_oculta() -> void:
	var tambor := _tambor()
	for numero in range(1, 11):
		_h.igual(
			tambor.estado_hueco(numero),
			TamborViewScript.EstadoHueco.OCULTO,
			"el hueco %d empieza oculto" % numero
		)


func _test_revelar_marca_bala_fatal_o_vacio() -> void:
	var tambor := _tambor()
	tambor.revelar(3, true)
	tambor.revelar(7, false)
	_h.igual(
		tambor.estado_hueco(3),
		TamborViewScript.EstadoHueco.BALA_FATAL,
		"el hueco disparado con bala queda como BALA_FATAL"
	)
	_h.igual(
		tambor.estado_hueco(7),
		TamborViewScript.EstadoHueco.VACIO,
		"el hueco disparado sin bala queda como VACIO"
	)


func _test_revelar_balas_destapa_el_resto_sin_pisar_lo_revelado() -> void:
	var tambor := _tambor()
	tambor.revelar(3, true)  # la bala que mata
	tambor.revelar(7, false)  # un vacio ya acertado antes
	tambor.revelar_balas([2, 3, 5])

	_h.igual(
		tambor.estado_hueco(3),
		TamborViewScript.EstadoHueco.BALA_FATAL,
		"la bala que mato sigue destacada, no se degrada a BALA"
	)
	_h.igual(
		tambor.estado_hueco(7),
		TamborViewScript.EstadoHueco.VACIO,
		"un vacio ya revelado no se convierte en bala"
	)
	for numero in [2, 5]:
		_h.igual(
			tambor.estado_hueco(numero),
			TamborViewScript.EstadoHueco.BALA,
			"la bala %d se destapa al perder" % numero
		)
	_h.igual(
		tambor.estado_hueco(1),
		TamborViewScript.EstadoHueco.OCULTO,
		"un hueco sin bala sigue oculto"
	)


func _test_numeros_fuera_del_tambor_no_revientan() -> void:
	var tambor := _tambor()
	tambor.revelar(0, true)
	tambor.revelar(99, false)
	tambor.revelar_balas([0, -4, 99])
	for numero in range(1, 11):
		_h.igual(
			tambor.estado_hueco(numero),
			TamborViewScript.EstadoHueco.OCULTO,
			"un numero fuera de rango no toca el hueco %d" % numero
		)
	_h.igual(
		tambor.estado_hueco(99),
		TamborViewScript.EstadoHueco.OCULTO,
		"preguntar fuera de rango da OCULTO"
	)
