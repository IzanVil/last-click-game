class_name Apuesta
extends RefCounted

var base: int
var en_juego: int


func _init(p_base: int) -> void:
	assert(p_base > 0, "La apuesta base debe ser un entero positivo.")
	base = p_base
	en_juego = p_base


func doblar() -> int:
	en_juego *= 2
	return en_juego


func perder() -> int:
	var perdidos := en_juego
	en_juego = 0
	return perdidos


func retirarse() -> int:
	return en_juego


func sumar_bono(cantidad: int) -> int:
	en_juego += cantidad
	return en_juego
