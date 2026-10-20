class_name Pista
extends RefCounted

var texto: String
var candidatos: Array[int]


func _init(p_texto: String, p_candidatos: Array[int]) -> void:
	texto = p_texto
	candidatos = p_candidatos
