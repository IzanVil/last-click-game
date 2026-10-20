class_name Azar
extends RefCounted

const MAXIMO := 4294967295


static func nueva() -> int:
	return randi()


static func generador(semilla: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = semilla
	return rng


static func parsear(texto: String) -> int:
	var limpio := texto.strip_edges()
	if limpio == "" or not limpio.is_valid_int():
		return -1
	var valor := limpio.to_int()
	if valor < 0 or valor > MAXIMO:
		return -1
	return valor


static func entero(rng: RandomNumberGenerator, desde: int, hasta: int) -> int:
	if rng != null:
		return rng.randi_range(desde, hasta)
	return randi_range(desde, hasta)


static func flotante(rng: RandomNumberGenerator) -> float:
	if rng != null:
		return rng.randf()
	return randf()
