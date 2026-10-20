class_name Jugador
extends RefCounted

var nombre: String
var apuesta: Apuesta
var farol: Farol
var historial: Historial
var disparos := 0

var puntos_finales := 0

var murio := false

var dias: int:
	get:
		return TamborJuicio.dias_sobrevividos(disparos - (1 if murio else 0))


func _init(p_nombre: String, p_apuesta: Apuesta, p_farol: Farol) -> void:
	nombre = p_nombre
	apuesta = p_apuesta
	farol = p_farol
	historial = Historial.new()


static func ganadores(jugadores: Array[Jugador]) -> Array[Jugador]:
	if jugadores.is_empty():
		return []

	var mejor_dias := jugadores[0].dias
	for jugador in jugadores:
		mejor_dias = maxi(mejor_dias, jugador.dias)
	var finalistas: Array[Jugador] = jugadores.filter(
		func(j: Jugador) -> bool: return j.dias == mejor_dias
	)
	if finalistas.size() == 1:
		return finalistas

	var mejores_puntos := finalistas[0].puntos_finales
	for jugador in finalistas:
		mejores_puntos = maxi(mejores_puntos, jugador.puntos_finales)
	return finalistas.filter(func(j: Jugador) -> bool: return j.puntos_finales == mejores_puntos)
