class_name Pista
extends RefCounted
## Una pista sobre la posicion de la bala: su texto y los huecos que esa
## misma afirmacion deja en pie (`candidatos`). No indica donde esta la
## bala de verdad: son los huecos consistentes con lo que el texto dice,
## sea o no mentira (ver Pistas.gd y el parametro `mentir`).

var texto: String
var candidatos: Array[int]


func _init(p_texto: String, p_candidatos: Array[int]) -> void:
	texto = p_texto
	candidatos = p_candidatos
