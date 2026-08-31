class_name RuletaEstado
extends RefCounted
## Orquestador de "El Tambor del Juicio": conecta TamborJuicio, Apuesta,
## Farol e Historial, y emite señales cuando pasa algo relevante.
##
## No conoce Label, ColorRect ni Tween: la vista (MainGame.gd) se conecta
## a esas señales y decide como mostrarlas. Hermano de terminal/ruleta.py,
## con la logica de disparar/marcar/retirarse que alli vive en jugar() y
## jugar_duelo().
##
## Una partida en solitario es, aqui, un duelo de un unico jugador: la
## misma logica sirve para los dos modos (ver `jugadores` y `turno`), y
## los atajos `apuesta`/`farol`/`historial`/`disparos` apuntan siempre al
## jugador activo, que en solitario es el unico que hay.
##
## Persistir records NO es cosa de este modulo (no toca disco): quien
## escuche `impacto`/`retirada`/`duelo_terminado` decide que hacer con el
## resultado, igual que en la version de terminal.

const HUECOS := 8
const DISPAROS_POR_DIA := TamborJuicio.DISPAROS_POR_DIA
const APUESTA_BASE := 100
const BONO_MARCA_ACERTADA := 50

## Se emite al empezar una partida nueva (tambor/apuesta/farol reseteados).
signal partida_iniciada(huecos: int, es_duelo: bool)
## Se emite cuando el numero elegido (disparo o marca) no esta en el tambor.
signal entrada_invalida(numero: int)
## Se emite cuando ocurre un evento aleatorio tras un disparo sobrevivido.
signal evento_ocurrido(tipo: String, texto: String)
## Se emite justo despues, con la pista nueva de ese disparo sobrevivido.
signal pista_nueva(texto: String, candidatos: Array)
## Se emite cuando un disparo real falla (sobrevive): la apuesta se dobla.
signal disparo_sobrevivido(disparos: int, en_juego: int)
## Se emite al completar un dia (cada DISPAROS_POR_DIA disparos sobrevividos).
signal dia_completado(dia: int)
## Se emite al resolver un farol, acierte o falle.
signal farol_resuelto(hueco: int, acierto: bool, en_juego: int, marcas_restantes: int)
## Se emite cuando un disparo real impacta en la bala. Fin de la partida.
signal impacto(disparos: int, perdidos: int, dias: int, resumen: String)
## Se emite al retirarse, cobrando lo que hay en juego. Fin de la partida.
signal retirada(disparos: int, ganados: int, dias: int, resumen: String)
## Solo en duelo: el turno pasa al otro jugador.
signal turno_cambiado(nombre: String, rival_nombre: String, rival_dias: int)
## Solo en duelo: tras impacto/retirada, con los jugadores ya comparados.
## Un empate total devuelve mas de un ganador (ver Jugador.ganadores).
signal duelo_terminado(jugadores: Array, ganadores: Array)

var tambor: TamborJuicio
var pistas_reveladas: Array[Pista] = []

## Todos los jugadores de la partida (uno en solitario, dos en duelo) y a
## quien le toca. El tambor y las pistas de arriba son compartidos: en un
## duelo los dos juegan literalmente el mismo revolver.
var jugadores: Array[Jugador] = []
var turno := 0

## Probabilidad de que ocurra un evento tras un disparo sobrevivido (ver
## Eventos.gd). Existe como propiedad, y no como la constante fija que
## usa MainGame.gd en el resto de casos, solo para poder desactivarla
## (a 0.0) en tests deterministas: GDScript no tiene un equivalente a
## unittest.mock.patch para sustituir Eventos.tirar_evento() por fuera.
var probabilidad_eventos := Eventos.PROBABILIDAD

## A quien le toca. Solo tiene sentido con una partida ya empezada: si
## se lee antes de iniciar_juego() no hay jugadores entre los que elegir
## (la vista se apoya en eso, ver MainGame._bloquear_acciones).
var jugador_activo: Jugador:
	get: return jugadores[turno % jugadores.size()]

# Atajos al jugador activo. En solitario "el jugador" es el unico que
# hay, asi que la vista y los tests siguen leyendo _estado.apuesta,
# _estado.disparos... igual que antes de existir el modo duelo.
var apuesta: Apuesta:
	get: return jugador_activo.apuesta
var farol: Farol:
	get: return jugador_activo.farol
var historial: Historial:
	get: return jugador_activo.historial
var disparos: int:
	get: return jugador_activo.disparos


## Una partida en solitario es un duelo de un solo jugador, asi que "es un
## duelo" es simplemente "hay mas de uno". De esto cuelga todo lo que
## distingue los dos modos: los turnos, el veredicto y hasta como se redacta
## el texto final.
func es_duelo() -> bool:
	return jugadores.size() > 1


## Empieza una partida. Con `nombres` vacio arranca una partida en
## solitario; con dos o mas nombres, un duelo por turnos.
func iniciar_juego(
	huecos: int = HUECOS,
	marcas: int = Farol.MARCAS_INICIALES,
	nombres: Array[String] = [],
) -> void:
	tambor = TamborJuicio.new(huecos)
	pistas_reveladas.clear()
	turno = 0
	jugadores.clear()

	if nombres.is_empty():
		jugadores.append(Jugador.new("", Apuesta.new(APUESTA_BASE), Farol.new(marcas)))
	else:
		for nombre in nombres:
			jugadores.append(Jugador.new(nombre, Apuesta.new(APUESTA_BASE), Farol.new(marcas)))

	partida_iniciada.emit(huecos, es_duelo())


## Resuelve un disparo real a `numero`. No decide temporizaciones ni
## reinicia la partida por si solo: eso queda en manos de quien escuche
## las señales (impacto/retirada marcan el fin; MainGame.gd decide que
## hacer despues).
func disparar(numero: int) -> void:
	if numero < 1 or numero > tambor.huecos:
		entrada_invalida.emit(numero)
		return

	var activo := jugador_activo
	activo.disparos += 1
	var impacto_ocurrido := tambor.disparar(numero)

	if impacto_ocurrido:
		activo.puntos_finales = activo.apuesta.perder()
		impacto.emit(
			activo.disparos,
			activo.puntos_finales,
			activo.dias,
			activo.historial.resumen(activo.dias),
		)
		_terminar_duelo_si_procede()
		return

	activo.apuesta.doblar()

	var evento := Eventos.tirar_evento(probabilidad_eventos)
	if evento == "clic_metalico":
		tambor.mover_extra()
	if evento != "":
		activo.historial.registrar_evento(evento)
		evento_ocurrido.emit(evento, Eventos.texto_de(evento))

	var pista := Pistas.generar_pista(
		tambor.posicion_bala, tambor.huecos, tambor.ultimo_disparo, "", evento == "tambor_caliente"
	)
	pistas_reveladas.append(pista)
	pista_nueva.emit(pista.texto, pista.candidatos)

	disparo_sobrevivido.emit(activo.disparos, activo.apuesta.en_juego)

	if activo.disparos % DISPAROS_POR_DIA == 0:
		dia_completado.emit(activo.dias)

	_avanzar_turno()


## Gasta una marca declarando `hueco` como seguro. Nunca mueve la bala
## ni termina la partida: solo dice si el jugador acerto (ver Farol.gd).
## En duelo si consume el turno, como en la version de terminal.
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


## Cobra los puntos en juego y termina la partida.
func retirarse() -> void:
	var activo := jugador_activo
	activo.puntos_finales = activo.apuesta.retirarse()
	retirada.emit(
		activo.disparos,
		activo.puntos_finales,
		activo.dias,
		activo.historial.resumen(activo.dias),
	)
	_terminar_duelo_si_procede()


func dias_sobrevividos() -> int:
	return jugador_activo.dias


## Pasa el turno. Se llama tras un disparo sobrevivido y tras un farol
## —marcar tambien consume turno, como en la version de terminal—, pero no
## tras un impacto o una retirada, que terminan la partida entera.
##
## En solitario el turno tambien avanza: `turno` cuenta acciones, y el
## jugador activo sigue siendo el unico que hay (ver jugador_activo).
func _avanzar_turno() -> void:
	turno += 1
	if not es_duelo():
		return
	var activo := jugador_activo
	var rival := jugadores[(turno + 1) % jugadores.size()]
	turno_cambiado.emit(activo.nombre, rival.nombre, rival.dias)


## El duelo acaba en cuanto el turno de uno de los dos termina en impacto
## o en retirada: el otro no sigue jugando en solitario despues.
func _terminar_duelo_si_procede() -> void:
	if not es_duelo():
		return
	# El rival no llego a jugar ese ultimo turno, asi que ni perdio ni
	# cobro: sus puntos finales son los que tenia en juego cuando el
	# duelo termino.
	for jugador in jugadores:
		if jugador != jugador_activo:
			jugador.puntos_finales = jugador.apuesta.en_juego
	duelo_terminado.emit(jugadores, Jugador.ganadores(jugadores))
