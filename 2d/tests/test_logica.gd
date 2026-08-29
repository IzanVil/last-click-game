extends SceneTree
## Smoke test headless de la logica pura de "El Tambor del Juicio" en
## Godot (TamborJuicio, Pistas, Apuesta, Farol, Eventos, Historial,
## RuletaEstado). Es el equivalente en GDScript a `terminal/test_*.py`:
## no hay framework de tests instalado en el proyecto (ni GUT ni nada
## similar), así que este script hace de arnes minimo, pensado para
## correr en CI vía:
##
##   godot --headless --script res://tests/test_logica.gd --path 2d
##
## Sale con exit code 0 si todo pasa, 1 si algo falla (y lo imprime).

var _fallos: Array[String] = []


func _init() -> void:
	_test_tambor_juicio_movimiento()
	_test_tambor_juicio_disparo()
	_test_pistas_candidatos()
	_test_pistas_interseccion()
	_test_apuesta()
	_test_farol()
	_test_eventos()
	_test_historial()
	_test_ruleta_estado_flujo_completo()

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
