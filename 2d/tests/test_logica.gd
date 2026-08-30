extends SceneTree
## Smoke test headless de la logica pura de "El Tambor del Juicio" en
## Godot (TamborJuicio, Pistas, Apuesta, Farol, Eventos, Historial,
## Records, Dificultad, Jugador, RuletaEstado). Es el equivalente en
## GDScript a `terminal/test_*.py`: no hay framework de tests instalado
## en el proyecto (ni GUT ni nada similar), así que este script hace de
## arnes minimo, pensado para correr en CI vía:
##
##   godot --headless --script res://tests/test_logica.gd --path 2d
##
## Sale con exit code 0 si todo pasa, 1 si algo falla (y lo imprime).

## Los tests de Records escriben de verdad en disco: se usa una ruta
## aparte de la real (Records.RUTA_POR_DEFECTO) para no pisar los
## records de quien ejecute los tests, y se borra al terminar.
const RUTA_RECORDS_TEST := "user://test_records_tmp.json"
const RUTA_AJUSTES_TEST := "user://test_ajustes_tmp.json"

var _fallos: Array[String] = []


func _init() -> void:
	_test_tambor_juicio_movimiento()
	_test_tambor_juicio_disparo()
	_test_dias_sobrevividos()
	_test_pistas_candidatos()
	_test_pistas_interseccion()
	_test_apuesta()
	_test_farol()
	_test_eventos()
	_test_historial()
	_test_dificultad()
	_test_records()
	_test_ajustes()
	_test_jugador_ganadores()
	_test_ruleta_estado_flujo_completo()
	_test_duelo_flujo_completo()
	_test_solitario_no_es_duelo()

	if _fallos.is_empty():
		print("OK: todos los tests de logica pasaron.")
		quit(0)
	else:
		print("FALLARON %d test(s):" % _fallos.size())
		for fallo in _fallos:
			print("  - ", fallo)
		quit(1)


func _afirmar(condicion: bool, descripcion: String) -> void:
	if not condicion:
		_fallos.append(descripcion)


func _afirmar_igual(obtenido, esperado, descripcion: String) -> void:
	if obtenido != esperado:
		_fallos.append("%s (obtenido=%s, esperado=%s)" % [descripcion, obtenido, esperado])


func _test_tambor_juicio_movimiento() -> void:
	var casos := [
		["avanza", 3, 4], ["avanza", 8, 1],
		["retrocede", 3, 2], ["retrocede", 1, 8],
		["salta_dos", 3, 5], ["salta_dos", 7, 1],
		["espejo", 3, 6],
	]
	for caso in casos:
		var tambor := TamborJuicio.new(8, caso[0], caso[1])
		tambor.disparar(1 if caso[1] != 1 else 2)  # falla a proposito
		_afirmar_igual(tambor.posicion_bala, caso[2], "movimiento '%s' desde %d" % [caso[0], caso[1]])


func _test_tambor_juicio_disparo() -> void:
	var tambor := TamborJuicio.new(8, "avanza", 3)
	_afirmar(tambor.disparar(3), "disparar a la posicion de la bala impacta")
	_afirmar_igual(tambor.posicion_bala, 3, "un impacto no mueve la bala")

	var otro := TamborJuicio.new(8, "avanza", 3)
	_afirmar(not otro.disparar(1), "disparar fuera de la bala no impacta")
	_afirmar_igual(otro.ultimo_disparo, 1, "ultimo_disparo se actualiza")
	_afirmar_igual(otro.historial, [1], "historial registra el disparo")

	var extra := TamborJuicio.new(8, "avanza", 3)
	extra.disparar(1)  # avanza a 4
	extra.mover_extra()  # avanza otra vez a 5
	_afirmar_igual(extra.posicion_bala, 5, "mover_extra desplaza fuera de un disparo")


func _test_pistas_candidatos() -> void:
	var par := Pistas.generar_pista(4, 8, -1, "paridad")
	_afirmar_igual(par.candidatos, [2, 4, 6, 8], "candidatos de una pista de paridad par")

	var mitad := Pistas.generar_pista(2, 8, -1, "mitad")
	_afirmar_igual(mitad.candidatos, [1, 2, 3, 4], "candidatos de mitad izquierda")

	var relativa := Pistas.generar_pista(2, 8, 5, "relativa")
	_afirmar_igual(relativa.candidatos, [1, 2, 3, 4], "candidatos de relativa a la izquierda")

	var mentira := Pistas.generar_pista(4, 8, -1, "paridad", true)
	_afirmar(mentira.texto.find("no esta en los huecos pares") != -1, "paridad mentirosa dice lo contrario")


func _test_pistas_interseccion() -> void:
	var pares := Pistas.generar_pista(4, 8, -1, "paridad")
	var izquierda := Pistas.generar_pista(2, 8, -1, "mitad")
	var cruce := Pistas.interseccion([pares, izquierda])
	_afirmar_igual(cruce, [2, 4], "interseccion de paridad par y mitad izquierda")

	var impar := Pistas.generar_pista(3, 8, -1, "paridad")
	var contradiccion := Pistas.interseccion([pares, impar])
	_afirmar(contradiccion.is_empty(), "pistas contradictorias dan interseccion vacia")

	_afirmar(Pistas.interseccion([]).is_empty(), "interseccion vacia sin pistas")


func _test_apuesta() -> void:
	var apuesta := Apuesta.new(100)
	_afirmar_igual(apuesta.en_juego, 100, "apuesta empieza con la base en juego")
	_afirmar_igual(apuesta.doblar(), 200, "doblar duplica lo que hay en juego")
	_afirmar_igual(apuesta.sumar_bono(50), 250, "sumar_bono suma sin doblar")
	_afirmar_igual(apuesta.perder(), 250, "perder devuelve todo lo que habia en juego")
	_afirmar_igual(apuesta.en_juego, 0, "perder deja la apuesta a cero")


func _test_farol() -> void:
	var marca := Farol.new(2)
	_afirmar(marca.marcar(3, 5), "marcar un hueco que no es la bala acierta")
	_afirmar_igual(marca.marcas_restantes, 1, "acertar tambien consume una marca")
	_afirmar(not marca.marcar(5, 5), "marcar justo la bala falla")
	_afirmar_igual(marca.marcas_restantes, 0, "fallar consume la ultima marca")
	_afirmar(not marca.puede_marcar(), "sin marcas no se puede marcar")


func _test_eventos() -> void:
	var nunca := Eventos.tirar_evento(0.0)
	_afirmar_igual(nunca, "", "probabilidad 0 nunca produce evento")
	var siempre := Eventos.tirar_evento(1.0)
	_afirmar(Eventos.TIPOS_EVENTO.has(siempre), "probabilidad 1 siempre produce un evento conocido")
	_afirmar(Eventos.texto_de("clic_metalico") != "", "hay texto para cada evento conocido")


func _test_historial() -> void:
	var vacio := Historial.new()
	_afirmar(vacio.resumen(2).find("sin faroles ni sobresaltos") != -1, "resumen sin faroles ni eventos")

	var lleno := Historial.new()
	lleno.registrar_farol(true)
	lleno.registrar_farol(false)
	lleno.registrar_evento("clic_metalico")
	var texto := lleno.resumen(5)
	_afirmar(texto.find("sobreviviste 5 dias") != -1, "resumen incluye los dias")
	_afirmar(texto.find("faroleaste 2 veces") != -1, "resumen cuenta los faroles")
	_afirmar(texto.find("1 acertado") != -1, "resumen cuenta los aciertos")
	_afirmar(texto.find("1 evento del tambor") != -1, "resumen cuenta los eventos")


## Ejercita RuletaEstado (el orquestador con señales) de punta a punta,
## en vez de solo sus piezas, para pillar errores de cableado entre
## señales que las pruebas unitarias de arriba no verian.
func _test_ruleta_estado_flujo_completo() -> void:
	var juego := RuletaEstado.new()

	var pistas_recibidas: Array[String] = []
	var dias_completados: Array[int] = []
	var retiradas: Array[Dictionary] = []

	juego.pista_nueva.connect(func(texto: String, _candidatos: Array): pistas_recibidas.append(texto))
	juego.dia_completado.connect(func(dia: int): dias_completados.append(dia))
	juego.retirada.connect(
		func(disparos: int, ganados: int, dias: int, resumen: String):
			retiradas.append({"disparos": disparos, "ganados": ganados, "dias": dias, "resumen": resumen})
	)

	juego.iniciar_juego(8)
	_afirmar_igual(juego.disparos, 0, "iniciar_juego arranca en 0 disparos")

	# Desactivamos los eventos aleatorios para este test: uno de tipo
	# "clic_metalico" podria mover la bala un paso de mas y hacerla
	# coincidir con el siguiente disparo de la secuencia fija de abajo,
	# lo que la volveria intermitente (ver probabilidad_eventos).
	juego.probabilidad_eventos = 0.0

	# Forzamos una bala que nunca esta en 1..7 para poder disparar 3
	# veces sin morir y comprobar el dia completo de forma deterministica.
	juego.tambor = TamborJuicio.new(8, "avanza", 8)
	for numero in [1, 2, 3]:
		juego.disparar(numero)

	_afirmar_igual(juego.disparos, 3, "3 disparos sobrevividos quedan registrados")
	_afirmar_igual(juego.apuesta.en_juego, 800, "3 disparos sobrevividos doblan 100 -> 800")
	_afirmar_igual(pistas_recibidas.size(), 3, "cada disparo sobrevivido emite una pista")
	_afirmar_igual(dias_completados, [1], "el tercer disparo completa el dia 1")

	juego.retirarse()
	_afirmar_igual(retiradas.size(), 1, "retirarse emite la señal retirada")
	if not retiradas.is_empty():
		_afirmar_igual(retiradas[0]["ganados"], 800, "retirarse cobra lo que habia en juego")
		_afirmar_igual(retiradas[0]["dias"], 1, "retirarse informa de los dias sobrevividos")


func _test_dias_sobrevividos() -> void:
	_afirmar_igual(TamborJuicio.dias_sobrevividos(0), 0, "0 disparos son 0 dias")
	_afirmar_igual(TamborJuicio.dias_sobrevividos(2), 0, "un dia a medias no cuenta")
	_afirmar_igual(TamborJuicio.dias_sobrevividos(3), 1, "3 disparos son 1 dia")
	_afirmar_igual(TamborJuicio.dias_sobrevividos(5), 1, "5 disparos siguen siendo 1 dia")
	_afirmar_igual(TamborJuicio.dias_sobrevividos(6), 2, "6 disparos son 2 dias")
	_afirmar_igual(
		TamborJuicio.dias_sobrevividos(4, 2), 2, "admite una duracion de dia distinta"
	)


func _test_dificultad() -> void:
	_afirmar_igual(Dificultad.ORDEN.size(), 3, "hay tres presets de dificultad")
	for clave in Dificultad.ORDEN:
		_afirmar(Dificultad.PRESETS.has(clave), "el preset '%s' existe en PRESETS" % clave)
		_afirmar(Dificultad.etiqueta_de(clave) != "", "el preset '%s' tiene etiqueta" % clave)

	_afirmar_igual(Dificultad.huecos_de("facil"), 10, "facil son 10 huecos")
	_afirmar_igual(Dificultad.marcas_de("facil"), 4, "facil son 4 marcas")
	_afirmar_igual(Dificultad.huecos_de("dificil"), 6, "dificil son 6 huecos")
	_afirmar_igual(Dificultad.marcas_de("dificil"), 2, "dificil son 2 marcas")

	# El preset normal no repite numeros a mano: sale de las constantes
	# que ya usaba el juego antes de existir la dificultad configurable.
	_afirmar_igual(
		Dificultad.huecos_de("normal"), RuletaEstado.HUECOS, "normal usa los huecos por defecto"
	)
	_afirmar_igual(
		Dificultad.marcas_de("normal"),
		Farol.MARCAS_INICIALES,
		"normal usa las marcas por defecto"
	)


func _test_records() -> void:
	var vacios := Records.new()
	_afirmar(
		vacios.resumen().find("Todavia no hay recuerdos") != -1,
		"sin partidas jugadas el resumen lo dice"
	)

	# Los maximos suben, pero nunca bajan; los acumulados suman siempre.
	var records := Records.new()
	records.registrar_partida(5, 800, 1, 1)
	records.registrar_partida(2, 100, 1, 0)
	_afirmar_igual(records.partidas_jugadas, 2, "cada partida cuenta")
	_afirmar_igual(records.dias_maximos, 5, "una partida peor no baja el maximo de dias")
	_afirmar_igual(records.puntos_maximos, 800, "una partida peor no baja el maximo de puntos")
	_afirmar_igual(records.faroles_usados, 2, "los faroles usados se acumulan")
	_afirmar_igual(records.faroles_acertados, 1, "los faroles acertados se acumulan")
	records.registrar_partida(9, 1600, 0, 0)
	_afirmar_igual(records.dias_maximos, 9, "una partida mejor si sube el maximo")

	var texto := records.resumen()
	_afirmar(texto.find("9 dia(s)") != -1, "el resumen incluye los dias maximos")
	_afirmar(texto.find("1600 puntos") != -1, "el resumen incluye los puntos maximos")
	_afirmar(texto.find("1/2") != -1, "el resumen incluye los faroles acertados/usados")
	_afirmar(texto.find("50%") != -1, "el resumen incluye el porcentaje de acierto")

	# Sin faroles el porcentaje no puede dividir por cero.
	var sin_faroles := Records.new()
	sin_faroles.registrar_partida(1, 100, 0, 0)
	_afirmar(sin_faroles.resumen().find("0/0") != -1, "sin faroles no divide por cero")

	_test_records_en_disco(records)


func _test_records_en_disco(records: Records) -> void:
	# Un archivo que no existe todavia (primera partida de siempre) no es
	# un error: devuelve records vacios.
	_borrar_records_test()
	var inexistente := Records.cargar(RUTA_RECORDS_TEST)
	_afirmar_igual(inexistente.partidas_jugadas, 0, "cargar sin archivo devuelve records vacios")

	_afirmar(records.guardar(RUTA_RECORDS_TEST), "guardar devuelve true al escribir bien")
	var recargados := Records.cargar(RUTA_RECORDS_TEST)
	_afirmar_igual(recargados.partidas_jugadas, records.partidas_jugadas, "recarga las partidas")
	_afirmar_igual(recargados.dias_maximos, records.dias_maximos, "recarga los dias maximos")
	_afirmar_igual(recargados.puntos_maximos, records.puntos_maximos, "recarga los puntos maximos")
	_afirmar_igual(recargados.faroles_usados, records.faroles_usados, "recarga los faroles usados")
	# Un JSON devuelve los numeros como float. Esto fija el contrato de
	# que, pese a ello, los campos recargados son enteros (hoy lo
	# garantizan por partida doble el int() de cargar() y el tipo
	# estatico de los campos, que convierte al asignar).
	_afirmar(
		typeof(recargados.dias_maximos) == TYPE_INT, "los numeros recargados son enteros, no floats"
	)

	# Un archivo corrupto tampoco debe impedir jugar.
	var archivo := FileAccess.open(RUTA_RECORDS_TEST, FileAccess.WRITE)
	archivo.store_string("esto no es json valido {{{")
	archivo.close()
	_afirmar_igual(
		Records.cargar(RUTA_RECORDS_TEST).partidas_jugadas,
		0,
		"un archivo corrupto devuelve records vacios"
	)

	# Ni un JSON valido que no sea un objeto.
	var archivo2 := FileAccess.open(RUTA_RECORDS_TEST, FileAccess.WRITE)
	archivo2.store_string("[1, 2, 3]")
	archivo2.close()
	_afirmar_igual(
		Records.cargar(RUTA_RECORDS_TEST).partidas_jugadas,
		0,
		"un JSON que no es un objeto devuelve records vacios"
	)

	# Claves desconocidas (p. ej. de una version futura) se ignoran sin
	# romper las que si se entienden.
	var archivo3 := FileAccess.open(RUTA_RECORDS_TEST, FileAccess.WRITE)
	archivo3.store_string('{"dias_maximos": 3, "campo_futuro": "x"}')
	archivo3.close()
	_afirmar_igual(
		Records.cargar(RUTA_RECORDS_TEST).dias_maximos, 3, "ignora claves desconocidas"
	)

	_borrar_records_test()


func _borrar_records_test() -> void:
	if FileAccess.file_exists(RUTA_RECORDS_TEST):
		DirAccess.remove_absolute(RUTA_RECORDS_TEST)


func _test_ajustes() -> void:
	var por_defecto := Ajustes.new()
	_afirmar(not por_defecto.efectos_reducidos, "por defecto los efectos estan activados")
	_afirmar(not por_defecto.texto_grande, "por defecto el texto es del tamano normal")
	_afirmar(not por_defecto.alto_contraste, "por defecto no hay alto contraste")
	_afirmar(por_defecto.sonido, "por defecto el juego suena")

	_borrar_ajustes_test()
	var inexistente := Ajustes.cargar(RUTA_AJUSTES_TEST)
	_afirmar(not inexistente.efectos_reducidos, "cargar sin archivo devuelve los ajustes de fabrica")
	_afirmar(inexistente.sonido, "y el sonido sigue puesto")

	var elegidos := Ajustes.new()
	elegidos.efectos_reducidos = true
	elegidos.texto_grande = true
	elegidos.sonido = false
	_afirmar(elegidos.guardar(RUTA_AJUSTES_TEST), "guardar devuelve true al escribir bien")

	var recargados := Ajustes.cargar(RUTA_AJUSTES_TEST)
	_afirmar(recargados.efectos_reducidos, "recarga los efectos reducidos")
	_afirmar(recargados.texto_grande, "recarga el texto grande")
	_afirmar(not recargados.alto_contraste, "recarga el contraste como estaba")
	_afirmar(not recargados.sonido, "recarga el sonido apagado")
	# Un JSON devuelve true/false como bool, pero el contrato es el mismo
	# que en Records: lo recargado tiene el tipo del campo, no el del JSON.
	_afirmar(
		typeof(recargados.efectos_reducidos) == TYPE_BOOL, "lo recargado son booleanos"
	)

	# Un archivo corrupto no debe impedir jugar: se vuelve a los de fabrica.
	var archivo := FileAccess.open(RUTA_AJUSTES_TEST, FileAccess.WRITE)
	archivo.store_string("esto no es json valido {{{")
	archivo.close()
	_afirmar(
		not Ajustes.cargar(RUTA_AJUSTES_TEST).efectos_reducidos,
		"un archivo de ajustes corrupto devuelve los de fabrica",
	)

	_borrar_ajustes_test()


func _borrar_ajustes_test() -> void:
	if FileAccess.file_exists(RUTA_AJUSTES_TEST):
		DirAccess.remove_absolute(RUTA_AJUSTES_TEST)


func _test_jugador_ganadores() -> void:
	var ana := Jugador.new("Ana", Apuesta.new(100), Farol.new())
	var beto := Jugador.new("Beto", Apuesta.new(100), Farol.new())

	# Sobrevivir mas dias manda, aunque el otro tenga mas puntos.
	ana.disparos = 6  # 2 dias
	ana.puntos_finales = 300
	beto.disparos = 3  # 1 dia
	beto.puntos_finales = 900
	var ganadores := Jugador.ganadores([ana, beto])
	_afirmar_igual(ganadores.size(), 1, "gana uno solo cuando hay mas dias")
	if ganadores.size() == 1:
		_afirmar_igual(ganadores[0].nombre, "Ana", "gana quien sobrevivio mas dias")

	# Con los mismos dias, desempatan los puntos.
	ana.disparos = 3
	ana.puntos_finales = 400
	beto.puntos_finales = 900
	ganadores = Jugador.ganadores([ana, beto])
	_afirmar_igual(ganadores.size(), 1, "el empate en dias lo rompe un solo ganador")
	if ganadores.size() == 1:
		_afirmar_igual(ganadores[0].nombre, "Beto", "con los mismos dias gana quien tiene mas puntos")

	# Mismos dias y mismos puntos: empate de verdad, sin ganador unico.
	ana.puntos_finales = 900
	_afirmar_igual(Jugador.ganadores([ana, beto]).size(), 2, "empate total deja dos ganadores")

	_afirmar(Jugador.ganadores([]).is_empty(), "sin jugadores no hay ganadores")


## Ejercita un duelo entero por señales: turnos alternos, tambor y pistas
## compartidos, y el veredicto al terminar.
func _test_duelo_flujo_completo() -> void:
	var juego := RuletaEstado.new()

	var turnos: Array[String] = []
	var duelos_terminados: Array[Dictionary] = []
	juego.turno_cambiado.connect(
		func(nombre: String, _rival: String, _rival_dias: int): turnos.append(nombre)
	)
	juego.duelo_terminado.connect(
		func(jugadores: Array, ganadores: Array):
			duelos_terminados.append({"jugadores": jugadores, "ganadores": ganadores})
	)

	juego.iniciar_juego(8, 3, ["Ana", "Beto"] as Array[String])
	_afirmar(juego.es_duelo(), "con dos nombres la partida es un duelo")
	_afirmar_igual(juego.jugadores.size(), 2, "hay dos jugadores")
	_afirmar_igual(juego.jugador_activo.nombre, "Ana", "empieza el primer jugador")

	juego.probabilidad_eventos = 0.0
	juego.tambor = TamborJuicio.new(8, "avanza", 8)  # la bala nunca esta en 1..7

	juego.disparar(1)  # Ana sobrevive
	_afirmar_igual(juego.jugador_activo.nombre, "Beto", "tras disparar pasa el turno")
	_afirmar_igual(turnos, ["Beto"] as Array[String], "el cambio de turno se anuncia")

	juego.disparar(2)  # Beto sobrevive
	_afirmar_igual(juego.jugador_activo.nombre, "Ana", "el turno vuelve al primero")

	# Cada jugador lleva su propia apuesta y sus propios disparos...
	_afirmar_igual(juego.jugadores[0].disparos, 1, "Ana lleva un disparo")
	_afirmar_igual(juego.jugadores[1].disparos, 1, "Beto lleva un disparo")
	_afirmar_igual(juego.jugadores[0].apuesta.en_juego, 200, "Ana doblo su apuesta")
	_afirmar_igual(juego.jugadores[1].apuesta.en_juego, 200, "Beto doblo la suya, aparte")
	# ...pero el tambor y sus pistas son compartidos.
	_afirmar_igual(juego.pistas_reveladas.size(), 2, "las pistas de ambos van al mismo monton")

	# Marcar tambien consume turno, y solo gasta las marcas de quien marca.
	juego.marcar(3)
	_afirmar_igual(juego.jugadores[0].farol.marcas_restantes, 2, "marcar gasta la marca de Ana")
	_afirmar_igual(juego.jugadores[1].farol.marcas_restantes, 3, "las marcas de Beto no se tocan")
	_afirmar_igual(juego.jugador_activo.nombre, "Beto", "marcar tambien pasa el turno")

	# Beto se retira: el duelo acaba ahi, Ana no sigue jugando sola.
	juego.retirarse()
	_afirmar_igual(duelos_terminados.size(), 1, "retirarse termina el duelo")
	if duelos_terminados.is_empty():
		return

	var jugadores: Array = duelos_terminados[0]["jugadores"]
	var ganadores: Array = duelos_terminados[0]["ganadores"]
	_afirmar_igual(jugadores[1].puntos_finales, 200, "quien se retira cobra lo que tenia en juego")
	# Ana no llego a jugar su ultimo turno: ni perdio ni cobro, se queda
	# con lo que tuviera en juego (200 doblados + 50 del farol acertado).
	_afirmar_igual(jugadores[0].puntos_finales, 250, "el rival congela los puntos que tenia")
	_afirmar_igual(ganadores.size(), 1, "con puntos distintos hay un unico ganador")
	if ganadores.size() == 1:
		_afirmar_igual(ganadores[0].nombre, "Ana", "gana quien acabo con mas puntos")


## Una partida en solitario es un duelo de un jugador: ni emite
## turno_cambiado ni duelo_terminado, y los atajos apuntan al unico que hay.
func _test_solitario_no_es_duelo() -> void:
	var juego := RuletaEstado.new()
	var turnos := 0
	var duelos := 0
	juego.turno_cambiado.connect(func(_n: String, _r: String, _d: int): turnos += 1)
	juego.duelo_terminado.connect(func(_j: Array, _g: Array): duelos += 1)

	juego.iniciar_juego(8)
	juego.probabilidad_eventos = 0.0
	juego.tambor = TamborJuicio.new(8, "avanza", 8)

	_afirmar(not juego.es_duelo(), "sin nombres la partida es en solitario")
	juego.disparar(1)
	juego.retirarse()
	_afirmar_igual(turnos, 0, "en solitario no se anuncian cambios de turno")
	_afirmar_igual(duelos, 0, "en solitario no se emite duelo_terminado")
