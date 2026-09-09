extends SceneTree
## Tests de RuletaEstado.gd, la logica pura del juego (sin nodos ni UI).
##
## Sin addons ni dependencias, igual que los tests de terminal/ usan solo
## unittest de la stdlib. Se lanzan asi:
##
##     godot --headless --script res://tests/test_ruleta_estado.gd --path 2d
##
## Salen con codigo 1 si algo falla, que es lo que mira la CI. Ojo: los
## casos invalidos de validar_dificultad() imprimen lineas "ERROR:" a
## proposito (son su push_error), asi que el veredicto va por exit code y
## no grepeando el log, al reves que el smoke test de la escena.

const RuletaEstado := preload("res://RuletaEstado.gd")

## Numero de repartos por ronda en la prueba de propiedades de las balas.
## Alto a proposito: el reparto es aleatorio y la propiedad ha de valer
## para cualquier barajado, no para uno con suerte.
const REPARTOS_POR_RONDA := 200

var _fallos: Array[String] = []
var _pasadas := 0


func _init() -> void:
	var nombres: Array[String] = []
	for metodo in get_method_list():
		if metodo.name.begins_with("_test_"):
			nombres.append(metodo.name)
	nombres.sort()

	print("Ejecutando %d tests de RuletaEstado...\n" % nombres.size())
	for nombre in nombres:
		call(nombre)

	if _fallos.is_empty():
		print("\nOK: %d comprobaciones en %d tests." % [_pasadas, nombres.size()])
		quit(0)
		return

	print("\nFALLOS (%d):" % _fallos.size())
	for fallo in _fallos:
		print("  - %s" % fallo)
	print("\n%d comprobaciones pasaron, %d fallaron." % [_pasadas, _fallos.size()])
	quit(1)


# --- Utilidades de test ------------------------------------------------


func _ok(condicion: bool, que: String) -> void:
	if condicion:
		_pasadas += 1
	else:
		_fallos.append(que)


func _igual(obtenido: Variant, esperado: Variant, que: String) -> void:
	_ok(obtenido == esperado, "%s | obtenido: %s | esperado: %s" % [que, obtenido, esperado])


## Apunta en orden toda senal que emita `estado`, como [nombre, args...].
## Asi un test puede comprobar no solo que se emitio lo que tocaba, sino
## que no se emitio nada de mas (que es justo lo que se escapa al mirar
## una senal suelta). Conectar dos veces el mismo estado duplicaria los
## eventos, asi que se llama una vez por estado.
func _grabar(estado: RuletaEstado) -> Array:
	var eventos: Array = []
	estado.ronda_preparada.connect(func(r, b, v): eventos.append(["ronda_preparada", r, b, v]))
	estado.entrada_invalida.connect(func(n): eventos.append(["entrada_invalida", n]))
	estado.impacto.connect(func(r, n): eventos.append(["impacto", r, n]))
	estado.click_seguro.connect(func(r, n): eventos.append(["click_seguro", r, n]))
	estado.partida_ganada.connect(func(r): eventos.append(["partida_ganada", r]))
	return eventos


## Un hueco sin bala de la ronda en curso. Los tests que quieren un
## "click" seguro no pueden elegir un numero fijo: las balas se reparten
## al azar en cada ronda.
func _hueco_vacio(estado: RuletaEstado) -> int:
	for hueco in range(1, RuletaEstado.HUECOS + 1):
		if hueco not in estado.posiciones_bala:
			return hueco
	return -1


## Lleva un estado recien iniciado hasta `ronda` sin disparar.
func _avanzar_hasta(estado: RuletaEstado, ronda: int) -> void:
	while estado.ronda_actual < ronda:
		estado.avanzar_ronda()


# --- Arranque y avance de rondas ---------------------------------------


func _test_iniciar_juego_arranca_en_la_ronda_1() -> void:
	var estado := RuletaEstado.new()
	var eventos := _grabar(estado)
	_ok(estado.iniciar_juego(), "iniciar_juego() devuelve true con la dificultad por defecto")
	_igual(estado.ronda_actual, 1, "arranca en la ronda 1")
	_igual(
		eventos,
		[["ronda_preparada", 1, 1, RuletaEstado.HUECOS - 1]],
		"iniciar_juego() emite solo ronda_preparada(1, 1, HUECOS-1)"
	)


func _test_cada_ronda_lleva_tantas_balas_como_su_numero() -> void:
	# Regresion de la tabla BALAS_POR_RONDA: era una lista de 8 elementos
	# que habia que mantener sincronizada a mano con RONDAS, y subir
	# RONDAS reventaba con un index out of range a mitad de partida. Se
	# recorre hasta la ultima ronda a proposito.
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	for ronda in range(1, RuletaEstado.RONDAS + 1):
		_avanzar_hasta(estado, ronda)
		_igual(estado.ronda_actual, ronda, "avanzar_ronda() llega a la ronda %d" % ronda)
		_igual(
			estado.posiciones_bala.size(), ronda, "la ronda %d reparte %d balas" % [ronda, ronda]
		)


func _test_ronda_preparada_informa_de_balas_y_vacios() -> void:
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	var eventos := _grabar(estado)
	estado.avanzar_ronda()
	_igual(
		eventos,
		[["ronda_preparada", 2, 2, RuletaEstado.HUECOS - 2]],
		"avanzar_ronda() emite ronda_preparada con balas y vacios cuadrados"
	)


# --- Reparto de balas ---------------------------------------------------


func _test_las_balas_son_unicas_y_caben_en_el_tambor() -> void:
	# Antes, _colocar_balas() sorteaba huecos reintentando los repetidos:
	# ademas de no terminar nunca si cantidad > HUECOS, era facil que un
	# cambio ahi colase duplicados sin que nadie se enterase.
	for ronda in range(1, RuletaEstado.RONDAS + 1):
		for _intento in range(REPARTOS_POR_RONDA):
			var estado := RuletaEstado.new()
			estado.ronda_actual = ronda
			estado.preparar_ronda()
			var balas := estado.posiciones_bala
			var unicas := {}
			for bala in balas:
				unicas[bala] = true
			if balas.size() != ronda or unicas.size() != ronda:
				_ok(
					false,
					(
						"ronda %d: %d balas, %d unicas -> %s"
						% [ronda, balas.size(), unicas.size(), balas]
					)
				)
				return
			for bala in balas:
				if not RuletaEstado.es_numero_valido(bala):
					_ok(false, "ronda %d: bala fuera del tambor -> %s" % [ronda, balas])
					return
	_ok(
		true,
		(
			"%d repartos por ronda: balas unicas, en cantidad y dentro de 1..HUECOS"
			% REPARTOS_POR_RONDA
		)
	)


func _test_el_reparto_sigue_siendo_array_int() -> void:
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	_igual(
		estado.posiciones_bala.get_typed_builtin(),
		TYPE_INT,
		"posiciones_bala es Array[int] y no un Array suelto"
	)


# --- Disparos -----------------------------------------------------------


func _test_es_numero_valido_en_las_fronteras() -> void:
	_ok(not RuletaEstado.es_numero_valido(0), "0 esta fuera del tambor")
	_ok(RuletaEstado.es_numero_valido(1), "1 es el primer hueco")
	_ok(RuletaEstado.es_numero_valido(RuletaEstado.HUECOS), "HUECOS es el ultimo hueco")
	_ok(
		not RuletaEstado.es_numero_valido(RuletaEstado.HUECOS + 1), "HUECOS+1 esta fuera del tambor"
	)


func _test_un_numero_fuera_del_tambor_solo_es_entrada_invalida() -> void:
	for numero in [0, -1, RuletaEstado.HUECOS + 1, 999]:
		var estado := RuletaEstado.new()
		estado.iniciar_juego()
		var eventos := _grabar(estado)
		estado.disparar(numero)
		_igual(
			eventos,
			[["entrada_invalida", numero]],
			"disparar(%d) emite entrada_invalida y nada mas" % numero
		)


func _test_disparar_a_una_bala_es_impacto() -> void:
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	var bala: int = estado.posiciones_bala[0]
	var eventos := _grabar(estado)
	estado.disparar(bala)
	_igual(eventos, [["impacto", 1, bala]], "disparar a una bala emite impacto y nada mas")


func _test_disparar_a_un_hueco_vacio_es_click_seguro() -> void:
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	var vacio := _hueco_vacio(estado)
	var eventos := _grabar(estado)
	estado.disparar(vacio)
	_igual(
		eventos,
		[["click_seguro", 1, vacio]],
		"un hueco vacio en la ronda 1 emite click_seguro y nada mas"
	)


func _test_disparar_no_avanza_de_ronda_por_su_cuenta() -> void:
	# Contrato documentado en RuletaEstado: quien avanza es la vista,
	# cuando ya termino de ensenar el resultado. Si disparar() avanzase
	# solo, la vista se comeria la ronda antes de mostrar nada.
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	var balas_antes := estado.posiciones_bala.duplicate()
	estado.disparar(_hueco_vacio(estado))
	_igual(estado.ronda_actual, 1, "tras un click seguro la ronda no cambia sola")
	_igual(estado.posiciones_bala, balas_antes, "tampoco se rebarajan las balas solas")


# --- Fin de partida -----------------------------------------------------


func _test_sobrevivir_la_ultima_ronda_gana_la_partida() -> void:
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	_avanzar_hasta(estado, RuletaEstado.RONDAS)
	var vacio := _hueco_vacio(estado)
	var eventos := _grabar(estado)
	estado.disparar(vacio)
	_igual(
		eventos,
		[
			["click_seguro", RuletaEstado.RONDAS, vacio],
			["partida_ganada", RuletaEstado.RONDAS],
		],
		"la ultima ronda emite click_seguro y, despues, partida_ganada"
	)


func _test_no_se_gana_antes_de_la_ultima_ronda() -> void:
	for ronda in range(1, RuletaEstado.RONDAS):
		var estado := RuletaEstado.new()
		estado.iniciar_juego()
		_avanzar_hasta(estado, ronda)
		var eventos := _grabar(estado)
		estado.disparar(_hueco_vacio(estado))
		var gano := false
		for evento in eventos:
			if evento[0] == "partida_ganada":
				gano = true
		_ok(
			not gano,
			"sobrevivir la ronda %d de %d no gana la partida" % [ronda, RuletaEstado.RONDAS]
		)


func _test_morir_no_emite_click_ni_victoria() -> void:
	var estado := RuletaEstado.new()
	estado.iniciar_juego()
	_avanzar_hasta(estado, RuletaEstado.RONDAS)
	var bala: int = estado.posiciones_bala[0]
	var eventos := _grabar(estado)
	estado.disparar(bala)
	_igual(
		eventos,
		[["impacto", RuletaEstado.RONDAS, bala]],
		"morir en la ultima ronda no cuela una victoria"
	)


# --- Dificultad ---------------------------------------------------------


func _test_validar_dificultad_acepta_lo_jugable() -> void:
	_ok(RuletaEstado.validar_dificultad(10, 8), "(huecos 10, rondas 8) es jugable")
	_ok(RuletaEstado.validar_dificultad(1, 1), "(huecos 1, rondas 1) es jugable")
	_ok(RuletaEstado.validar_dificultad(10, 10), "(huecos 10, rondas 10) es jugable")


func _test_validar_dificultad_rechaza_lo_imposible() -> void:
	# Estos cuatro casos imprimen "ERROR:" por su push_error. Es lo
	# esperado, no un fallo del test.
	print("  (los siguientes ERROR son parte del test de dificultad invalida)")
	_ok(not RuletaEstado.validar_dificultad(0, 1), "sin huecos no hay tambor")
	_ok(not RuletaEstado.validar_dificultad(-3, 2), "huecos negativos no valen")
	_ok(not RuletaEstado.validar_dificultad(10, 0), "sin rondas no hay partida")
	_ok(not RuletaEstado.validar_dificultad(5, 6), "la ronda 6 no cabe en un tambor de 5")


func _test_la_dificultad_del_juego_es_jugable() -> void:
	# El bug que se quiere evitar: tocar HUECOS/RONDAS y dejar el juego
	# roto sin enterarse hasta el final de una partida real.
	_ok(
		RuletaEstado.validar_dificultad(RuletaEstado.HUECOS, RuletaEstado.RONDAS),
		(
			"HUECOS=%d y RONDAS=%d forman una dificultad jugable"
			% [RuletaEstado.HUECOS, RuletaEstado.RONDAS]
		)
	)


func _test_la_ultima_ronda_deja_algun_hueco_vacio() -> void:
	# validar_dificultad() permite RONDAS == HUECOS (no es incoherente),
	# pero en ese caso la ultima ronda va con el tambor lleno y la partida
	# es imposible de ganar. Con las constantes actuales quedan huecos de
	# sobra; esto salta si alguien las acerca demasiado.
	_ok(
		RuletaEstado.RONDAS < RuletaEstado.HUECOS,
		(
			"la ultima ronda deja huecos vacios: RONDAS(%d) < HUECOS(%d)"
			% [RuletaEstado.RONDAS, RuletaEstado.HUECOS]
		)
	)
