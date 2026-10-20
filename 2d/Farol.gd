class_name Farol
extends RefCounted

const MARCAS_INICIALES := 3

var marcas_restantes: int


func _init(p_marcas: int = MARCAS_INICIALES) -> void:
	assert(p_marcas >= 0, "El numero de marcas no puede ser negativo.")
	marcas_restantes = p_marcas


func puede_marcar() -> bool:
	return marcas_restantes > 0


func marcar(hueco: int, posicion_bala: int) -> bool:
	assert(puede_marcar(), "No quedan marcas disponibles.")
	marcas_restantes -= 1
	return hueco != posicion_bala
