class_name Pistas
extends RefCounted
## Generacion de pistas sobre la posicion de la bala.
##
## Hermano de terminal/pistas.py: por defecto las pistas son veraces;
## con `mentir = true` (lo pide el evento "tambor_caliente", ver
## Eventos.gd) afirman justo lo contrario, con el mismo aspecto que una
## veraz. Todo estatico: este modulo no lleva estado propio.

const TIPOS_PISTA: Array[String] = ["paridad", "mitad", "relativa"]


## `tipo == ""` sortea uno entre los disponibles; la pista "relativa"
## (respecto al ultimo disparo) solo puede salir si `ultimo_disparo` no
## es -1 (sin disparo previo, ver TamborJuicio.ultimo_disparo).
static func generar_pista(
	posicion_bala: int,
	huecos: int,
	ultimo_disparo: int = -1,
	tipo: String = "",
	mentir: bool = false,
) -> Pista:
	var elegido := tipo
	if elegido == "":
		var disponibles := TIPOS_PISTA.duplicate()
		if ultimo_disparo == -1:
			disponibles.erase("relativa")
		elegido = disponibles[randi() % disponibles.size()]

	match elegido:
		"paridad":
			var par := posicion_bala % 2 == 0
			if mentir:
				par = not par
			if par:
				return Pista.new("La bala descansa en un hueco par.", _por_paridad(huecos, true))
			return Pista.new("La bala no esta en los huecos pares.", _por_paridad(huecos, false))

		"mitad":
			var mitad := huecos / 2
			var izquierda := posicion_bala <= mitad
			if mentir:
				izquierda = not izquierda
			if izquierda:
				return Pista.new(
					"La bala esta en la mitad izquierda del tambor.",
					_por_mitad(huecos, mitad, true)
				)
			return Pista.new(
				"La bala esta en la mitad derecha del tambor.", _por_mitad(huecos, mitad, false)
			)

		"relativa":
			assert(ultimo_disparo != -1, "No hay disparo previo para dar una pista relativa.")
			if posicion_bala == ultimo_disparo:
				# Ocurre de verdad, y ni siquiera es raro: la bala se mueve
				# DESPUES de un disparo fallido (ver TamborJuicio.disparar),
				# asi que puede acabar justo en el hueco que se acaba de
				# probar; con el patron "avanza" basta con disparar un hueco
				# por delante de ella. Y aqui `mentir` si tiene un opuesto
				# claro: si la bala esta exactamente en el ultimo disparo,
				# cualquiera de los dos lados es falso. Antes esta rama lo
				# ignoraba, de modo que un evento "tambor_caliente" -que
				# existe justo para mentir- acababa regalando la posicion
				# exacta de la bala.
				if not mentir:
					return Pista.new(
						"La bala esta justo donde acabas de disparar.", [ultimo_disparo]
					)
				# Se miente hacia un lado que exista: disparar al hueco 1 (o
				# al ultimo) deja un lado sin ningun hueco, y una pista con
				# cero candidatos se delataria sola al cruzarla.
				var lados: Array[bool] = []
				if ultimo_disparo > 1:
					lados.append(true)
				if ultimo_disparo < huecos:
					lados.append(false)
				var miente_a_la_izquierda: bool = lados[randi() % lados.size()]
				if miente_a_la_izquierda:
					return Pista.new(
						"La bala esta a la izquierda de tu ultimo disparo.",
						_por_relativa(huecos, ultimo_disparo, true)
					)
				return Pista.new(
					"La bala esta a la derecha de tu ultimo disparo.",
					_por_relativa(huecos, ultimo_disparo, false)
				)
			var izquierda := posicion_bala < ultimo_disparo
			if mentir:
				izquierda = not izquierda
			if izquierda:
				return Pista.new(
					"La bala esta a la izquierda de tu ultimo disparo.",
					_por_relativa(huecos, ultimo_disparo, true)
				)
			return Pista.new(
				"La bala esta a la derecha de tu ultimo disparo.",
				_por_relativa(huecos, ultimo_disparo, false)
			)

		_:
			push_error("Tipo de pista desconocido: %s" % elegido)
			return Pista.new("", [])


## Cruza los candidatos de varias pistas. Vacio si `pistas` esta vacio,
## o si las que hay se contradicen entre si (senal de que alguna, por un
## evento "tambor_caliente", pudo ser mentira).
static func interseccion(pistas: Array[Pista]) -> Array[int]:
	if pistas.is_empty():
		return []
	var resultado: Array[int] = pistas[0].candidatos.duplicate()
	for i in range(1, pistas.size()):
		var candidatos_pista := pistas[i].candidatos
		resultado = resultado.filter(func(h: int) -> bool: return candidatos_pista.has(h))
	return resultado


## Estos tres metodos traducen una pista a la lista de huecos que la
## cumplen. Esa lista es lo unico que la vista necesita para colorear el
## tambor, y lo que interseccion() cruza cuando hay varias pistas vigentes:
## por eso una pista mentirosa no necesita ningun tratamiento especial aqui,
## basta con darle los candidatos de la afirmacion contraria.
static func _por_paridad(huecos: int, par: bool) -> Array[int]:
	var resultado: Array[int] = []
	for h in range(1, huecos + 1):
		if (h % 2 == 0) == par:
			resultado.append(h)
	return resultado


static func _por_mitad(huecos: int, mitad: int, izquierda: bool) -> Array[int]:
	var resultado: Array[int] = []
	for h in range(1, huecos + 1):
		if (h <= mitad) == izquierda:
			resultado.append(h)
	return resultado


static func _por_relativa(huecos: int, ultimo_disparo: int, izquierda: bool) -> Array[int]:
	var resultado: Array[int] = []
	for h in range(1, huecos + 1):
		# A un lado en sentido estricto: el propio hueco disparado no esta
		# ni a la izquierda ni a la derecha de si mismo. La condicion
		# anterior, "(h < ultimo_disparo) == izquierda", equivalia a
		# h >= ultimo_disparo en la rama derecha y colaba ahi el hueco
		# recien disparado, que la pista precisamente descarta (en
		# terminal/pistas.py la comparacion ya era estricta).
		var cumple := h < ultimo_disparo if izquierda else h > ultimo_disparo
		if cumple:
			resultado.append(h)
	return resultado
