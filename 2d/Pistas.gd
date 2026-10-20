class_name Pistas
extends RefCounted

const TIPOS_PISTA: Array[String] = ["paridad", "mitad", "relativa"]


static func generar_pista(
	posicion_bala: int,
	huecos: int,
	ultimo_disparo: int = -1,
	tipo: String = "",
	mentir: bool = false,
	rng: RandomNumberGenerator = null,
) -> Pista:
	var elegido := tipo
	if elegido == "":
		var disponibles := TIPOS_PISTA.duplicate()
		if ultimo_disparo == -1:
			disponibles.erase("relativa")
		elegido = disponibles[Azar.entero(rng, 0, disponibles.size() - 1)]

	match elegido:
		"paridad":
			return _pista_paridad(posicion_bala, huecos, mentir)
		"mitad":
			return _pista_mitad(posicion_bala, huecos, mentir)
		"relativa":
			assert(ultimo_disparo != -1, "No hay disparo previo para dar una pista relativa.")
			return _pista_relativa(posicion_bala, huecos, ultimo_disparo, mentir, rng)
		_:
			push_error("Tipo de pista desconocido: %s" % elegido)
			return Pista.new("", [])


static func interseccion(pistas: Array[Pista]) -> Array[int]:
	if pistas.is_empty():
		return []
	var resultado: Array[int] = pistas[0].candidatos.duplicate()
	for i in range(1, pistas.size()):
		var candidatos_pista := pistas[i].candidatos
		resultado = resultado.filter(func(h: int) -> bool: return candidatos_pista.has(h))
	return resultado


static func _pista_paridad(posicion_bala: int, huecos: int, mentir: bool) -> Pista:
	var par := (posicion_bala % 2 == 0) != mentir
	if par:
		return Pista.new("La bala descansa en un hueco par.", _por_paridad(huecos, true))
	return Pista.new("La bala no esta en los huecos pares.", _por_paridad(huecos, false))


static func _pista_mitad(posicion_bala: int, huecos: int, mentir: bool) -> Pista:
	var mitad := huecos / 2
	var izquierda := (posicion_bala <= mitad) != mentir
	if izquierda:
		return Pista.new(
			"La bala esta en la mitad izquierda del tambor.", _por_mitad(huecos, mitad, true)
		)
	return Pista.new(
		"La bala esta en la mitad derecha del tambor.", _por_mitad(huecos, mitad, false)
	)


static func _pista_relativa(
	posicion_bala: int, huecos: int, ultimo_disparo: int, mentir: bool, rng: RandomNumberGenerator
) -> Pista:
	var izquierda: bool
	if posicion_bala == ultimo_disparo:
		if not mentir:
			return Pista.new("La bala esta justo donde acabas de disparar.", [ultimo_disparo])
		izquierda = _lado_al_azar(huecos, ultimo_disparo, rng)
	else:
		izquierda = (posicion_bala < ultimo_disparo) != mentir

	if izquierda:
		return Pista.new(
			"La bala esta a la izquierda de tu ultimo disparo.",
			_por_relativa(huecos, ultimo_disparo, true)
		)
	return Pista.new(
		"La bala esta a la derecha de tu ultimo disparo.",
		_por_relativa(huecos, ultimo_disparo, false)
	)


static func _lado_al_azar(huecos: int, ultimo_disparo: int, rng: RandomNumberGenerator) -> bool:
	var lados: Array[bool] = []
	if ultimo_disparo > 1:
		lados.append(true)
	if ultimo_disparo < huecos:
		lados.append(false)
	return lados[Azar.entero(rng, 0, lados.size() - 1)]


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
		var cumple := h < ultimo_disparo if izquierda else h > ultimo_disparo
		if cumple:
			resultado.append(h)
	return resultado
