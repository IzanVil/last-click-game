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
					"La bala esta en la mitad izquierda del tambor.", _por_mitad(huecos, mitad, true)
				)
			return Pista.new(
				"La bala esta en la mitad derecha del tambor.", _por_mitad(huecos, mitad, false)
			)

		"relativa":
			assert(ultimo_disparo != -1, "No hay disparo previo para dar una pista relativa.")
			if posicion_bala == ultimo_disparo:
				# No deberia ocurrir en la practica: si coincidieran habria
				# sido un impacto y la partida ya habria terminado antes
				# de pedir pista. `mentir` no tiene un opuesto claro aqui.
				return Pista.new("La bala esta justo donde acabas de disparar.", [ultimo_disparo])
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
		if (h < ultimo_disparo) == izquierda:
			resultado.append(h)
	return resultado
