class_name Apuesta
extends RefCounted
## Puntos en juego durante la partida actual: doblar o retirarse.
##
## Hermano de terminal/apuestas.py. La partida arranca con una apuesta
## base ya "en juego"; tras cada disparo que sobrevive, los puntos en
## juego se doblan.

var base: int
var en_juego: int


func _init(p_base: int) -> void:
	assert(p_base > 0, "La apuesta base debe ser un entero positivo.")
	base = p_base
	en_juego = p_base


## Duplica los puntos en juego tras sobrevivir un disparo.
func doblar() -> int:
	en_juego *= 2
	return en_juego


## Pierde todos los puntos en juego. Devuelve la cantidad perdida.
func perder() -> int:
	var perdidos := en_juego
	en_juego = 0
	return perdidos


## Cierra la apuesta sin arriesgar mas. Devuelve lo que se cobra.
func retirarse() -> int:
	return en_juego


## Suma puntos extra sin doblar (p. ej. un farol acertado).
func sumar_bono(cantidad: int) -> int:
	en_juego += cantidad
	return en_juego
