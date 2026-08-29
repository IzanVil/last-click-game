class_name Farol
extends RefCounted
## Marcas disponibles durante la partida actual: marcar un hueco como
## seguro sin disparar.
##
## Hermano de terminal/farol.py. Marcar consume una marca acierte o
## falle. A diferencia de un disparo, marcar nunca mueve la bala ni
## termina la partida: solo dice si el jugador acerto, para que pueda
## validar una deduccion sin arriesgar el pellejo.

const MARCAS_INICIALES := 3

var marcas_restantes: int


func _init(p_marcas: int = MARCAS_INICIALES) -> void:
	assert(p_marcas >= 0, "El numero de marcas no puede ser negativo.")
	marcas_restantes = p_marcas


func puede_marcar() -> bool:
	return marcas_restantes > 0


## Gasta una marca declarando `hueco` como seguro. Devuelve true si
## acierta (la bala no estaba ahi). Consume la marca tanto si acierta
## como si falla: es el coste de preguntar.
func marcar(hueco: int, posicion_bala: int) -> bool:
	assert(puede_marcar(), "No quedan marcas disponibles.")
	marcas_restantes -= 1
	return hueco != posicion_bala
