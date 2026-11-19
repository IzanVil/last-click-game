class_name Sonido
extends RefCounted

enum Efecto { DISPARO, VICTORIA, DERROTA, ENGRANAJE, MARCA, FALLO, CLIC, CALOR }

const BUS_MUSICA := "Musica"
const BUS_EFECTOS := "Efectos"

const VOLUMEN_MUSICA_MENU := -20.0
const VOLUMEN_MUSICA_PARTIDA := -13.0
const VOLUMEN_SILENCIO := -80.0

const HUECOS_PARA_TENSION := 3
const ACELERACION_MAXIMA := 0.10

const NODOS_DE_EFECTOS := {
	Efecto.DISPARO: "SonidoDisparo",
	Efecto.VICTORIA: "SonidoVictoria",
	Efecto.DERROTA: "SonidoDerrota",
	Efecto.ENGRANAJE: "SonidoEngranaje",
	Efecto.MARCA: "SonidoMarca",
	Efecto.FALLO: "SonidoFallo",
	Efecto.CLIC: "SonidoClic",
	Efecto.CALOR: "SonidoCalor",
}

var ajustes := Ajustes.new()

var _anfitrion: Node
var _musica_base: AudioStreamPlayer
var _musica_tension: AudioStreamPlayer
var _efectos := {}


func _init(anfitrion: Node) -> void:
	_anfitrion = anfitrion
	_musica_base = anfitrion.get_node("MusicaBase") as AudioStreamPlayer
	_musica_tension = anfitrion.get_node("MusicaTension") as AudioStreamPlayer
	for efecto in NODOS_DE_EFECTOS:
		_efectos[efecto] = anfitrion.get_node(NODOS_DE_EFECTOS[efecto]) as AudioStreamPlayer
	_preparar_buses()


static func plan_de_musica(en_partida: bool, libres: int, total: int) -> Dictionary:
	var apretado := 1.0 - float(libres) / float(maxi(total, 1))
	var hay_tension := en_partida and libres <= HUECOS_PARA_TENSION
	return {
		"base": VOLUMEN_MUSICA_PARTIDA if en_partida else VOLUMEN_MUSICA_MENU,
		"tension": VOLUMEN_MUSICA_PARTIDA - 4.0 if hay_tension else VOLUMEN_SILENCIO,
		"ritmo": 1.0 + ACELERACION_MAXIMA * apretado if en_partida else 1.0,
	}


func reproducir(efecto: Efecto) -> void:
	if ajustes.sonido:
		(_efectos[efecto] as AudioStreamPlayer).play()


func aplicar_volumenes() -> void:
	var mezclas := {
		BUS_MUSICA: ajustes.volumen_musica,
		BUS_EFECTOS: ajustes.volumen_efectos,
	}
	for nombre in mezclas:
		var indice := AudioServer.get_bus_index(nombre)
		if indice == -1:
			continue
		var valor: float = mezclas[nombre]
		AudioServer.set_bus_mute(indice, valor <= 0.001)
		AudioServer.set_bus_volume_db(indice, linear_to_db(maxf(valor, 0.001)))


func arrancar_musica() -> bool:
	if not ajustes.sonido or DisplayServer.get_name() == "headless":
		return false
	for reproductor in [_musica_base, _musica_tension]:
		_poner_en_bucle(reproductor)
		reproductor.volume_db = VOLUMEN_SILENCIO
		reproductor.play()
	return true


func musica_sonando() -> bool:
	return _musica_base.playing


func parar_musica() -> void:
	_musica_base.stop()
	_musica_tension.stop()


func ajustar_musica(en_partida: bool, libres: int, total: int, duracion: float = 1.0) -> void:
	if not _musica_base.playing:
		return

	var plan := plan_de_musica(en_partida, libres, total)
	var tween := _anfitrion.create_tween().set_parallel(true)
	tween.tween_property(_musica_base, "volume_db", plan["base"], duracion)
	tween.tween_property(_musica_tension, "volume_db", plan["tension"], duracion)
	for reproductor in [_musica_base, _musica_tension]:
		tween.tween_property(reproductor, "pitch_scale", plan["ritmo"], duracion)


func liberar() -> void:
	for reproductor in [_musica_base, _musica_tension]:
		reproductor.stop()
		reproductor.stream = null


func _preparar_buses() -> void:
	for nombre in [BUS_MUSICA, BUS_EFECTOS]:
		if AudioServer.get_bus_index(nombre) != -1:
			continue
		AudioServer.add_bus()
		var indice := AudioServer.bus_count - 1
		AudioServer.set_bus_name(indice, nombre)
		AudioServer.set_bus_send(indice, "Master")

	for reproductor in [_musica_base, _musica_tension]:
		reproductor.bus = BUS_MUSICA
	for efecto in _efectos:
		(_efectos[efecto] as AudioStreamPlayer).bus = BUS_EFECTOS


func _poner_en_bucle(reproductor: AudioStreamPlayer) -> void:
	var flujo := reproductor.stream as AudioStreamWAV
	if flujo == null or flujo.loop_mode == AudioStreamWAV.LOOP_FORWARD:
		return
	flujo.loop_mode = AudioStreamWAV.LOOP_FORWARD
	flujo.loop_begin = 0
	flujo.loop_end = int(flujo.get_length() * flujo.mix_rate)
