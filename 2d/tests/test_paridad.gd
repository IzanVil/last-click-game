extends SceneTree
## Comprueba que esta version dice exactamente lo mismo que la de Python.
##
## Cada modulo de 2d/ tiene un hermano en terminal/ con la misma mecanica
## escrita a mano en GDScript, y hasta ahora lo unico que lo garantizaba
## era un comentario que decia "hermano de X.py". No bastaba: al escribir
## los tests de la semilla aparecieron dos divergencias en Pistas.gd que
## llevaban ahi desde el principio.
##
## terminal/paridad.py genera una tabla de casos con la respuesta que da
## la version de Python; este script la replica aqui y compara. Se corre
## en CI via:
##
##   godot --headless --script res://tests/test_paridad.gd --path 2d
##
## Sale con exit code 0 si todo coincide, 1 si algo no. Si falla, lo
## primero que hay que mirar es cual de las dos versiones tiene razon:
## la tabla es la foto de lo que hace Python, no un oraculo.
##
## Regenerar la tabla tras un cambio deliberado de reglas:
##
##   python3 terminal/paridad.py

const RUTA_TABLA := "res://tests/paridad.json"

## Formato de tabla que este script sabe leer. Si Python sube el suyo sin
## que se actualice esto, el test falla en vez de comparar a medias.
const FORMATO := 2

var _fallos: Array[String] = []
var _comparaciones := 0

## Cuantos casos de cada seccion se han llegado a recorrer. Godot sale con
## exit code 0 aunque un script reviente a media ejecucion (solo lo
## imprime como SCRIPT ERROR), asi que sin esto un error en mitad de
## _test_pistas dejaba el test diciendo "OK" con una fraccion de los
## casos comparados. Se comprueba al final contra el tamaño de cada lista
## de la tabla: si falta uno, es que no se llego hasta el final.
var _vistos: Dictionary = {}


func _init() -> void:
	var tabla := _cargar_tabla()
	if tabla.is_empty():
		quit(1)
		return

	_test_constantes(tabla["constantes"])
	_test_mover(tabla["mover"])
	_test_dias(tabla["dias"])
	_test_pistas(tabla["pistas"])
	_test_interseccion(tabla["interseccion"])
	_test_apuesta(tabla["apuesta"])
	_test_farol(tabla["farol"])
	_test_resumen(tabla["resumen"])
	_test_ganadores(tabla["ganadores"])
	_comprobar_que_se_recorrio_todo(tabla)

	if _fallos.is_empty():
		print("OK: las dos versiones coinciden en %d comparaciones." % _comparaciones)
		quit(0)
	else:
		print("DIVERGENCIAS entre la version de Godot y la de Python (%d):" % _fallos.size())
		# Se imprimen todas y no solo la primera: si una regla cambio en
		# un lado, normalmente arrastra decenas de casos, y verlos juntos
		# dice cual es la regla mucho mejor que verlos de uno en uno.
		for fallo in _fallos.slice(0, 40):
			print("  - ", fallo)
		if _fallos.size() > 40:
			print("  ... y %d mas." % (_fallos.size() - 40))
		quit(1)


## Ninguna seccion puede quedarse a medias sin que se note.
func _comprobar_que_se_recorrio_todo(tabla: Dictionary) -> void:
	for seccion: String in [
		"mover", "dias", "pistas", "interseccion", "apuesta", "farol", "resumen", "ganadores"
	]:
		var esperados: int = (tabla[seccion] as Array).size()
		var recorridos: int = _vistos.get(seccion, 0)
		if recorridos != esperados:
			_fallos.append(
				(
					"la seccion '%s' se quedo a medias: %d de %d casos (¿error de script?)"
					% [seccion, recorridos, esperados]
				)
			)


func _cargar_tabla() -> Dictionary:
	if not FileAccess.file_exists(RUTA_TABLA):
		print(
			(
				"FALTA la tabla de paridad en %s (generala con `python3 terminal/paridad.py`)."
				% RUTA_TABLA
			)
		)
		return {}
	var crudo := FileAccess.get_file_as_string(RUTA_TABLA)
	var leido: Variant = JSON.parse_string(crudo)
	if typeof(leido) != TYPE_DICTIONARY:
		print("La tabla de paridad no es un JSON valido.")
		return {}
	var tabla: Dictionary = leido
	if int(tabla.get("formato", -1)) != FORMATO:
		print(
			(
				"La tabla de paridad es del formato %s y este script lee el %d."
				% [tabla.get("formato", "?"), FORMATO]
			)
		)
		return {}
	return tabla


func _afirmar_igual(obtenido: Variant, esperado: Variant, que: String) -> void:
	_comparaciones += 1
	if obtenido != esperado:
		_fallos.append("%s: Godot dice %s y Python dice %s" % [que, obtenido, esperado])


## JSON.parse_string devuelve todo numero como float, asi que cualquier
## entero que venga de la tabla hay que convertirlo antes de compararlo
## con uno de GDScript (1.0 != 1 al comparar Variants de distinto tipo).
func _enteros(lista: Array) -> Array[int]:
	var salida: Array[int] = []
	for valor in lista:
		salida.append(int(valor))
	return salida


func _test_constantes(c: Dictionary) -> void:
	_afirmar_igual(RuletaEstado.HUECOS, int(c["huecos"]), "HUECOS")
	_afirmar_igual(TamborJuicio.DISPAROS_POR_DIA, int(c["disparos_por_dia"]), "DISPAROS_POR_DIA")
	_afirmar_igual(TamborJuicio.PATRONES, _textos(c["patrones"]), "PATRONES")
	_afirmar_igual(Pistas.TIPOS_PISTA, _textos(c["tipos_pista"]), "TIPOS_PISTA")
	_afirmar_igual(Eventos.TIPOS_EVENTO, _textos(c["tipos_evento"]), "TIPOS_EVENTO")
	_afirmar_igual(Eventos.PROBABILIDAD, float(c["probabilidad_evento"]), "PROBABILIDAD")
	_afirmar_igual(Farol.MARCAS_INICIALES, int(c["marcas_iniciales"]), "MARCAS_INICIALES")
	_afirmar_igual(RuletaEstado.APUESTA_BASE, int(c["apuesta_base"]), "APUESTA_BASE")
	_afirmar_igual(
		RuletaEstado.BONO_MARCA_ACERTADA, int(c["bono_marca_acertada"]), "BONO_MARCA_ACERTADA"
	)

	for tipo: String in c["textos_evento"]:
		_afirmar_igual(
			Eventos.texto_de(tipo), str(c["textos_evento"][tipo]), "texto del evento '%s'" % tipo
		)

	for nombre: String in c["dificultades"]:
		var preset: Dictionary = c["dificultades"][nombre]
		_afirmar_igual(
			Dificultad.huecos_de(nombre), int(preset["huecos"]), "huecos de '%s'" % nombre
		)
		_afirmar_igual(
			Dificultad.marcas_de(nombre), int(preset["marcas"]), "marcas de '%s'" % nombre
		)


func _textos(lista: Array) -> Array[String]:
	var salida: Array[String] = []
	for valor in lista:
		salida.append(str(valor))
	return salida


func _test_mover(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["mover"] = int(_vistos.get("mover", 0)) + 1
		var huecos := int(caso["huecos"])
		var patron := str(caso["patron"])
		var posicion := int(caso["posicion"])
		_afirmar_igual(
			TamborJuicio._mover(posicion, patron, huecos),
			int(caso["resultado"]),
			"mover %d con '%s' en un tambor de %d" % [posicion, patron, huecos]
		)


func _test_dias(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["dias"] = int(_vistos.get("dias", 0)) + 1
		var disparos := int(caso["disparos"])
		_afirmar_igual(
			TamborJuicio.dias_sobrevividos(disparos),
			int(caso["resultado"]),
			"dias de %d disparos" % disparos
		)


## Una pista puede tener mas de una respuesta valida: la relativa
## mentirosa con la bala justo en el ultimo disparo elige lado al azar.
## Por eso se compara contra una lista de posibles y no contra una sola.
func _test_pistas(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["pistas"] = int(_vistos.get("pistas", 0)) + 1
		var huecos := int(caso["huecos"])
		var posicion := int(caso["posicion"])
		var ultimo := int(caso["ultimo"])
		var tipo := str(caso["tipo"])
		var mentir: bool = caso["mentir"]

		var pista := Pistas.generar_pista(posicion, huecos, ultimo, tipo, mentir)
		var obtenido := {"texto": pista.texto, "candidatos": pista.candidatos}

		var posibles: Array = caso["posibles"]
		var coincide := false
		var esperados: Array[String] = []
		for posible: Dictionary in posibles:
			var candidatos := _enteros(posible["candidatos"])
			esperados.append("%s %s" % [posible["texto"], candidatos])
			if pista.texto == str(posible["texto"]) and pista.candidatos == candidatos:
				coincide = true

		_comparaciones += 1
		if not coincide:
			(
				_fallos
				. append(
					(
						"pista %s (bala %d, ultimo %d, %d huecos, mentir=%s): Godot dice '%s' %s y Python admite %s"
						% [
							tipo,
							posicion,
							ultimo,
							huecos,
							mentir,
							obtenido["texto"],
							obtenido["candidatos"],
							esperados
						]
					)
				)
			)


func _test_interseccion(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["interseccion"] = int(_vistos.get("interseccion", 0)) + 1
		var lista: Array[Pista] = []
		for candidatos: Array in caso["candidatos"]:
			lista.append(Pista.new("", _enteros(candidatos)))
		var obtenido := Pistas.interseccion(lista)
		obtenido.sort()
		_afirmar_igual(
			obtenido, _enteros(caso["resultado"]), "interseccion de %s" % [caso["candidatos"]]
		)


func _test_apuesta(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["apuesta"] = int(_vistos.get("apuesta", 0)) + 1
		var apuesta := Apuesta.new(RuletaEstado.APUESTA_BASE)
		var devueltos: Array[int] = []
		for paso: String in caso["guion"]:
			match paso:
				"doblar":
					devueltos.append(apuesta.doblar())
				"bono":
					devueltos.append(apuesta.sumar_bono(RuletaEstado.BONO_MARCA_ACERTADA))
				"perder":
					devueltos.append(apuesta.perder())
				_:
					devueltos.append(apuesta.retirarse())
		_afirmar_igual(
			devueltos, _enteros(caso["devueltos"]), "apuesta %s (devueltos)" % [caso["guion"]]
		)
		_afirmar_igual(
			apuesta.en_juego, int(caso["en_juego"]), "apuesta %s (en juego)" % [caso["guion"]]
		)


func _test_farol(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["farol"] = int(_vistos.get("farol", 0)) + 1
		var marca := Farol.new(int(caso["marcas"]))
		var bala := int(caso["bala"])
		var aciertos: Array[bool] = []
		for hueco: float in caso["huecos"]:
			aciertos.append(marca.marcar(int(hueco), bala))
		var esperados: Array[bool] = []
		for valor: bool in caso["aciertos"]:
			esperados.append(valor)
		_afirmar_igual(aciertos, esperados, "farol %s (aciertos)" % [caso["huecos"]])
		_afirmar_igual(
			marca.marcas_restantes,
			int(caso["restantes"]),
			"farol %s (restantes)" % [caso["huecos"]]
		)
		_afirmar_igual(
			marca.puede_marcar(), caso["puede_marcar"], "farol %s (puede_marcar)" % [caso["huecos"]]
		)


func _test_resumen(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["resumen"] = int(_vistos.get("resumen", 0)) + 1
		var bitacora := Historial.new()
		bitacora.faroles_usados = int(caso["faroles_usados"])
		bitacora.faroles_acertados = int(caso["faroles_acertados"])
		for tipo: String in caso["eventos"]:
			bitacora.eventos[tipo] = int(caso["eventos"][tipo])
		_afirmar_igual(
			bitacora.resumen(int(caso["dias"])),
			str(caso["resultado"]),
			(
				"resumen de %d dias, %d faroles, eventos %s"
				% [int(caso["dias"]), bitacora.faroles_usados, caso["eventos"]]
			)
		)


## El desempate de un duelo: mandan los dias y, si empatan, los puntos.
## Un empate total devuelve mas de un ganador.
func _test_ganadores(casos: Array) -> void:
	for caso: Dictionary in casos:
		_vistos["ganadores"] = int(_vistos.get("ganadores", 0)) + 1
		var jugadores: Array[Jugador] = []
		for fila: Dictionary in caso["mesa"]:
			var uno := Jugador.new("", Apuesta.new(100), Farol.new(3))
			uno.disparos = int(fila["dias"]) * TamborJuicio.DISPAROS_POR_DIA
			uno.puntos_finales = int(fila["puntos"])
			jugadores.append(uno)
		var indices: Array[int] = []
		for vencedor in Jugador.ganadores(jugadores):
			indices.append(jugadores.find(vencedor))
		_afirmar_igual(indices, _enteros(caso["ganadores"]), "ganadores de %s" % [caso["mesa"]])
