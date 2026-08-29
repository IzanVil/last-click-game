class_name RuletaEstado
extends RefCounted
## Orquestador de "El Tambor del Juicio": conecta TamborJuicio, Apuesta,
## Farol e Historial, y emite señales cuando pasa algo relevante.
##
## No conoce Label, ColorRect ni Tween: la vista (MainGame.gd) se conecta
## a esas señales y decide como mostrarlas. Hermano de terminal/ruleta.py,
## con la logica de disparar/marcar/retirarse que alli vive en jugar().

const HUECOS := 8
const DISPAROS_POR_DIA := 3
const APUESTA_BASE := 100
const BONO_MARCA_ACERTADA := 50

## Se emite al empezar una partida nueva (tambor/apuesta/farol reseteados).
signal partida_iniciada(huecos: int)
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

var tambor: TamborJuicio
var apuesta: Apuesta
var farol: Farol
var historial: Historial
var disparos := 0
var pistas_reveladas: Array[Pista] = []

## Probabilidad de que ocurra un evento tras un disparo sobrevivido (ver
## Eventos.gd). Existe como propiedad, y no como la constante fija que
## usa MainGame.gd en el resto de casos, solo para poder desactivarla
## (a 0.0) en tests deterministas: GDScript no tiene un equivalente a
## unittest.mock.patch para sustituir Eventos.tirar_evento() por fuera.
var probabilidad_eventos := Eventos.PROBABILIDAD


func iniciar_juego(huecos: int = HUECOS) -> void:
	tambor = TamborJuicio.new(huecos)
	apuesta = Apuesta.new(APUESTA_BASE)
	farol = Farol.new()
	historial = Historial.new()
	disparos = 0
	pistas_reveladas.clear()
	partida_iniciada.emit(huecos)


## Resuelve un disparo real a `numero`. No decide temporizaciones ni
## reinicia la partida por si solo: eso queda en manos de quien escuche
## las señales (impacto/retirada marcan el fin; MainGame.gd decide
## cuando volver a llamar a iniciar_juego()).
func disparar(numero: int) -> void:
	if numero < 1 or numero > tambor.huecos:
		entrada_invalida.emit(numero)
		return

	disparos += 1
	var impacto_ocurrido := tambor.disparar(numero)

	if impacto_ocurrido:
		var perdidos := apuesta.perder()
		var dias := dias_sobrevividos()
		impacto.emit(disparos, perdidos, dias, historial.resumen(dias))
		return

	apuesta.doblar()

	var evento := Eventos.tirar_evento(probabilidad_eventos)
	if evento == "clic_metalico":
		tambor.mover_extra()
	if evento != "":
		historial.registrar_evento(evento)
		evento_ocurrido.emit(evento, Eventos.texto_de(evento))

	var pista := Pistas.generar_pista(
		tambor.posicion_bala, tambor.huecos, tambor.ultimo_disparo, "", evento == "tambor_caliente"
	)
	pistas_reveladas.append(pista)
	pista_nueva.emit(pista.texto, pista.candidatos)

	disparo_sobrevivido.emit(disparos, apuesta.en_juego)

	if disparos % DISPAROS_POR_DIA == 0:
		dia_completado.emit(dias_sobrevividos())


## Gasta una marca declarando `hueco` como seguro. Nunca mueve la bala
## ni termina la partida: solo dice si el jugador acerto (ver Farol.gd).
func marcar(hueco: int) -> void:
	if hueco < 1 or hueco > tambor.huecos:
		entrada_invalida.emit(hueco)
		return

	var acierto := farol.marcar(hueco, tambor.posicion_bala)
	historial.registrar_farol(acierto)
	if acierto:
		apuesta.sumar_bono(BONO_MARCA_ACERTADA)
	farol_resuelto.emit(hueco, acierto, apuesta.en_juego, farol.marcas_restantes)


## Cobra los puntos en juego y termina la partida.
func retirarse() -> void:
	var ganados := apuesta.retirarse()
	var dias := dias_sobrevividos()
	retirada.emit(disparos, ganados, dias, historial.resumen(dias))


func dias_sobrevividos() -> int:
	return disparos / DISPAROS_POR_DIA
