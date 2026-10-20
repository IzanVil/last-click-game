class_name RuletaEstado
extends RefCounted

const HUECOS := 8
const DISPAROS_POR_DIA := TamborJuicio.DISPAROS_POR_DIA
const APUESTA_BASE := 100
const BONO_MARCA_ACERTADA := 50

signal partida_iniciada(huecos: int, es_duelo: bool)
signal entrada_invalida(numero: int)
signal evento_ocurrido(tipo: String, texto: String)
signal pista_nueva(texto: String, candidatos: Array)
signal disparo_sobrevivido(disparos: int, en_juego: int)
signal dia_completado(dia: int)
signal farol_resuelto(hueco: int, acierto: bool, en_juego: int, marcas_restantes: int)
signal impacto(disparos: int, perdidos: int, dias: int, resumen: String)
signal retirada(disparos: int, ganados: int, dias: int, resumen: String)
signal turno_cambiado(nombre: String, rival_nombre: String, rival_dias: int)
signal duelo_terminado(jugadores: Array, ganadores: Array)

var tambor: TamborJuicio
var pistas_reveladas: Array[Pista] = []

var semilla := -1
var _azar: RandomNumberGenerator = null

var jugadores: Array[Jugador] = []
var turno := 0

var probabilidad_eventos := Eventos.PROBABILIDAD

var jugador_activo: Jugador:
	get:
		return jugadores[turno % jugadores.size()]

var apuesta: Apuesta:
	get:
		return jugador_activo.apuesta
var farol: Farol:
	get:
		return jugador_activo.farol
var historial: Historial:
	get:
		return jugador_activo.historial
var disparos: int:
	get:
		return jugador_activo.disparos


func es_duelo() -> bool:
	return jugadores.size() > 1


func iniciar_juego(
	huecos: int = HUECOS,
	marcas: int = Farol.MARCAS_INICIALES,
	nombres: Array[String] = [],
	semilla_pedida: int = -1,
) -> void:
	semilla = semilla_pedida if semilla_pedida >= 0 else Azar.nueva()
	_azar = Azar.generador(semilla)
	tambor = TamborJuicio.new(huecos, "", -1, _azar)
	pistas_reveladas.clear()
	turno = 0
	jugadores.clear()

	if nombres.is_empty():
		jugadores.append(Jugador.new("", Apuesta.new(APUESTA_BASE), Farol.new(marcas)))
	else:
		for nombre in nombres:
			jugadores.append(Jugador.new(nombre, Apuesta.new(APUESTA_BASE), Farol.new(marcas)))

	partida_iniciada.emit(huecos, es_duelo())


func disparar(numero: int) -> void:
	if numero < 1 or numero > tambor.huecos:
		entrada_invalida.emit(numero)
		return

	var activo := jugador_activo
	activo.disparos += 1
	var impacto_ocurrido := tambor.disparar(numero)

	if impacto_ocurrido:
		activo.murio = true
		var perdidos := activo.apuesta.perder()
		activo.puntos_finales = 0
		(
			impacto
			. emit(
				activo.disparos,
				perdidos,
				activo.dias,
				activo.historial.resumen(activo.dias),
			)
		)
		_terminar_duelo_si_procede()
		return

	activo.apuesta.doblar()

	var evento := Eventos.tirar_evento(probabilidad_eventos, _azar)
	if evento == "clic_metalico":
		tambor.mover_extra()
	if evento != "":
		activo.historial.registrar_evento(evento)
		evento_ocurrido.emit(evento, Eventos.texto_de(evento))

	var pista := Pistas.generar_pista(
		tambor.posicion_bala,
		tambor.huecos,
		tambor.ultimo_disparo,
		"",
		evento == "tambor_caliente",
		_azar
	)
	pistas_reveladas.append(pista)
	pista_nueva.emit(pista.texto, pista.candidatos)

	disparo_sobrevivido.emit(activo.disparos, activo.apuesta.en_juego)

	if activo.disparos % DISPAROS_POR_DIA == 0:
		dia_completado.emit(activo.dias)

	_avanzar_turno()


func marcar(hueco: int) -> void:
	if hueco < 1 or hueco > tambor.huecos:
		entrada_invalida.emit(hueco)
		return

	var activo := jugador_activo
	var acierto := activo.farol.marcar(hueco, tambor.posicion_bala)
	activo.historial.registrar_farol(acierto)
	if acierto:
		activo.apuesta.sumar_bono(BONO_MARCA_ACERTADA)
	farol_resuelto.emit(hueco, acierto, activo.apuesta.en_juego, activo.farol.marcas_restantes)

	_avanzar_turno()


func retirarse() -> void:
	var activo := jugador_activo
	activo.puntos_finales = activo.apuesta.retirarse()
	(
		retirada
		. emit(
			activo.disparos,
			activo.puntos_finales,
			activo.dias,
			activo.historial.resumen(activo.dias),
		)
	)
	_terminar_duelo_si_procede()


func dias_sobrevividos() -> int:
	return jugador_activo.dias


func _avanzar_turno() -> void:
	turno += 1
	if not es_duelo():
		return
	var activo := jugador_activo
	var rival := jugadores[(turno + 1) % jugadores.size()]
	turno_cambiado.emit(activo.nombre, rival.nombre, rival.dias)


func _terminar_duelo_si_procede() -> void:
	if not es_duelo():
		return
	for jugador in jugadores:
		if jugador != jugador_activo:
			jugador.puntos_finales = jugador.apuesta.en_juego
	duelo_terminado.emit(jugadores, Jugador.ganadores(jugadores))
