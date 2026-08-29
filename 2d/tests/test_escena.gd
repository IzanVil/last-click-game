extends SceneTree
## Test de integracion headless: carga la escena real (MainGame.tscn) y
## simula una partida completa pulsando los mismos metodos que los
## botones (_on_disparar_btn_pressed, _on_marcar_btn_pressed,
## _on_retirarse_btn_pressed), esperando de verdad a que las animaciones
## (Tween) terminen entre una accion y la siguiente.
##
## A diferencia de test_logica.gd (que prueba RuletaEstado y sus modulos
## de logica pura de forma aislada, sin nodos), este ejercita tambien el
## cableado de señales de MainGame.gd: la parte que test_logica.gd no
## toca. Uso:
##
##   godot --headless --script res://tests/test_escena.gd --path 2d

const ESCENA := preload("res://scenes/MainGame.tscn")

var _main
var _fallos: Array[String] = []


func _init() -> void:
	_main = ESCENA.instantiate()
	root.add_child(_main)
	await process_frame  # deja que corra _ready() y sus @onready

	await _forzar_bala_lejos()
	await _simular_marcar_acierto()
	await _simular_marcar_fallo()
	await _simular_disparo_seguro()
	await _simular_impacto()
	await _simular_retirada()

	if _fallos.is_empty():
		print("OK: la escena responde a disparar/marcar/retirarse sin errores.")
		quit(0)
	else:
		print("FALLARON %d comprobacion(es):" % _fallos.size())
		for fallo in _fallos:
			print("  - ", fallo)
		quit(1)


func _afirmar(condicion: bool, descripcion: String) -> void:
	if not condicion:
		_fallos.append(descripcion)


## Sustituye el tambor sorteado por uno determinista (bala lejos de los
## huecos 1-3 que vamos a usar) para poder simular sin depender del azar.
func _forzar_bala_lejos() -> void:
	_main._estado.tambor = TamborJuicio.new(8, "avanza", 8)
	_afirmar(_main._estado.tambor.posicion_bala == 8, "el tambor forzado empieza en el hueco 8")


func _simular_marcar_acierto() -> void:
	_main.entrada_numero.text = "1"
	_main._on_marcar_btn_pressed()
	await process_frame
	await create_timer(0.6).timeout  # tension() dura 0.5s
	_afirmar(_main._estado.farol.marcas_restantes == 2, "marcar acertado consume una marca")
	_afirmar(_main._estado.apuesta.en_juego == 150, "marcar acertado suma el bono (100 -> 150)")
	_afirmar(
		_main._resultados_farol.get(1) == TamborView.EstadoHueco.SEGURO,
		"el hueco marcado y acertado queda en verde",
	)


func _simular_marcar_fallo() -> void:
	_main.entrada_numero.text = "8"  # ahi esta la bala de verdad
	_main._on_marcar_btn_pressed()
	await process_frame
	await create_timer(0.6).timeout
	_afirmar(_main._estado.farol.marcas_restantes == 1, "marcar fallido tambien consume la marca")
	_afirmar(_main._estado.apuesta.en_juego == 150, "marcar fallido no toca los puntos")
	_afirmar(
		_main._resultados_farol.get(8) == TamborView.EstadoHueco.PELIGRO,
		"el hueco marcado y fallado queda en rojo",
	)


func _simular_disparo_seguro() -> void:
	_main.entrada_numero.text = "2"  # falla: la bala sigue en 8
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(0.6).timeout
	_afirmar(_main._estado.disparos == 1, "el disparo fallido cuenta como disparo sobrevivido")
	_afirmar(_main._estado.apuesta.en_juego == 300, "un disparo sobrevivido dobla lo que hay en juego")
	_afirmar(_main._marcadas.has(2), "el hueco disparado queda registrado como probado")
	_afirmar(not _main._accion_bloqueada, "tras resolver el disparo, las acciones se desbloquean")


func _simular_impacto() -> void:
	_main._estado.tambor = TamborJuicio.new(8, "avanza", 3)
	_main.entrada_numero.text = "3"  # justo la bala
	_main._on_disparar_btn_pressed()
	await process_frame
	await create_timer(1.0).timeout  # tension() (0.5s) + margen hasta _on_impacto
	_afirmar(_main._accion_bloqueada, "tras un impacto, las acciones quedan bloqueadas")
	await create_timer(2.0).timeout  # 1.6s de pausa en _on_impacto + margen
	_afirmar(_main._estado.disparos == 0, "tras la pausa del impacto, la partida se ha reiniciado")
	_afirmar(_main._estado.apuesta.en_juego == 100, "la partida nueva tras morir vuelve a la apuesta base")


func _simular_retirada() -> void:
	_main._on_retirarse_btn_pressed()
	await process_frame
	_afirmar(_main._accion_bloqueada, "retirarse bloquea la interfaz mientras se reinicia")
	await create_timer(3.2).timeout  # 2.5s de pausa de _on_retirada + margen
	_afirmar(_main._estado.disparos == 0, "tras la pausa de retirada, la partida se ha reiniciado")
	_afirmar(_main._estado.apuesta.en_juego == 100, "la partida nueva vuelve a la apuesta base")
