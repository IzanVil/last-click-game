class_name Azar
extends RefCounted
## Semilla de partida: el numero que hace repetible una partida entera.
##
## Hermano de terminal/semillas.py, con el mismo rango de semillas para
## que un numero apuntado en una version se pueda teclear en la otra.
##
## Ojo con lo que ESO significa hoy: la misma semilla da la misma partida
## dentro de la misma version, no entre las dos. Python usa Mersenne
## Twister y Godot usa PCG32, asi que la secuencia de numeros no coincide
## aunque la semilla si. Igualar eso es cosa de un generador compartido,
## no de este modulo.
##
## `entero()` y `flotante()` son el equivalente del `rng or random` de
## Python: con un generador de partida se usa ese, y sin el se cae al
## azar global del motor, que es lo que hacia todo el codigo antes de
## que existieran las semillas.

## 2^32 - 1: corto de teclear a mano y comun a las dos versiones.
const MAXIMO := 4294967295


## Sortea una semilla nueva dentro del rango valido.
static func nueva() -> int:
	return randi_range(0, MAXIMO)


## Devuelve el generador de una partida a partir de su semilla.
static func generador(semilla: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = semilla
	return rng


## Lee una semilla escrita a mano. Devuelve -1 -el mismo "no hay" que
## usan ultimo_disparo y posicion_inicial en TamborJuicio- si el texto
## esta vacio o no es un numero valido: en el menu, una semilla mal
## escrita no debe impedir jugar, solo dejar que se sortee una.
static func parsear(texto: String) -> int:
	var limpio := texto.strip_edges()
	if limpio == "" or not limpio.is_valid_int():
		return -1
	var valor := limpio.to_int()
	if valor < 0 or valor > MAXIMO:
		return -1
	return valor


## Un entero entre `desde` y `hasta`, ambos incluidos.
static func entero(rng: RandomNumberGenerator, desde: int, hasta: int) -> int:
	if rng != null:
		return rng.randi_range(desde, hasta)
	return randi_range(desde, hasta)


## Un flotante en [0, 1).
static func flotante(rng: RandomNumberGenerator) -> float:
	if rng != null:
		return rng.randf()
	return randf()
