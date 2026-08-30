class_name Jugador
extends RefCounted
## Un jugador dentro de una partida: su apuesta, sus marcas de farol, su
## historial y sus disparos.
##
## Hermano de ruleta.JugadorDuelo en la version de terminal. Aqui se usa
## tambien en la partida en solitario (que es, simplemente, un duelo con
## un unico jugador), asi que se llama solo `Jugador`.
##
## El tambor, su patron y las pistas NO viven aqui: son compartidos por
## todos los jugadores de la partida y los lleva RuletaEstado (en un
## duelo es literalmente el mismo revolver).

var nombre: String
var apuesta: Apuesta
var farol: Farol
var historial: Historial
var disparos := 0

## Puntos con los que este jugador termina la partida. Lo fija
## RuletaEstado al morir (0), al retirarse (lo cobrado) o, para el rival
## que no llego a jugar su ultimo turno, lo que tuviera en juego.
var puntos_finales := 0

var dias: int:
	get: return TamborJuicio.dias_sobrevividos(disparos)


func _init(p_nombre: String, p_apuesta: Apuesta, p_farol: Farol) -> void:
	nombre = p_nombre
	apuesta = p_apuesta
	farol = p_farol
	historial = Historial.new()


## Decide quien gana entre varios jugadores: sobrevivir mas dias manda, y
## en caso de empate desempatan los puntos. Devuelve una lista porque un
## empate total (mismos dias y mismos puntos) no tiene ganador unico.
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
