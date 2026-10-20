extends SceneTree

const ESCENA := preload("res://scenes/MainGame.tscn")

const MARGEN := 46.0

var _main


func _captura(nombre: String, nodo_marco: Control) -> void:
	for etiqueta in [_main.etiqueta_resultado, _main.fin_resumen, _main.ayuda_texto]:
		Maquina.completar(etiqueta)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var imagen := root.get_texture().get_image()
	var escala := Vector2(imagen.get_size()) / root.get_visible_rect().size
	var caja := nodo_marco.get_global_rect().grow(MARGEN)
	var recorte := Rect2i(
		Vector2i((caja.position * escala).floor()), Vector2i((caja.size * escala).ceil())
	)
	recorte = recorte.intersection(Rect2i(Vector2i.ZERO, imagen.get_size()))
	imagen.get_region(recorte).save_png("user://" + nombre)
	print("guardada ", nombre, " ", recorte.size)


func _init() -> void:
	_main = ESCENA.instantiate()
	_main.ruta_records = "user://shot_records.json"
	_main.ruta_ajustes = "user://shot_ajustes.json"
	root.add_child(_main)
	await process_frame
	var marco: Control = _main.get_node("Centro/Marco")
	await create_timer(1.2).timeout
	await _captura("menu.png", marco)

	_main._alternar_pausa()
	await create_timer(0.4).timeout
	await _captura("ajustes.png", _main.get_node("Pausa/Centro/Marco"))
	_main._on_cerrar_pausa_pressed()

	_main._on_empezar_btn_pressed()
	await create_timer(2.0).timeout
	_main._estado.tambor = TamborJuicio.new(8, "salta_dos", 8)
	_main._estado.probabilidad_eventos = 0.0
	for numero in ["1", "5", "3"]:
		_main.entrada_numero.text = numero
		_main._on_disparar_btn_pressed()
		await create_timer(2.2).timeout
	_main._estado.pistas_reveladas.clear()
	_main._estado.pistas_reveladas.append(Pistas.generar_pista(4, 8, -1, "paridad"))
	_main._estado.pistas_reveladas.append(Pistas.generar_pista(4, 8, -1, "mitad"))
	_main._refrescar_pistas()
	_main.tambor.aplicar_estados(_main._calcular_estados())
	_main._on_hueco_pulsado(4)
	await create_timer(0.6).timeout
	await _captura("partida.png", marco)

	_main._on_evento_ocurrido("tambor_caliente", Eventos.texto_de("tambor_caliente"))
	_main._on_pista_nueva("La bala esta en un hueco par.", [2, 4, 6, 8])
	await create_timer(1.3).timeout
	_main.fondo_taller.calentar()
	_main.vineta.resplandor(Paleta.ROJO, 1.6)
	var huecos: Array[int] = [2, 4, 6, 8]
	_main.tambor.destello(huecos)
	await create_timer(0.35).timeout
	await _captura("tambor-caliente.png", marco)

	_main._estado.tambor = TamborJuicio.new(8, "avanza", 7)
	_main.entrada_numero.text = "7"
	_main._on_disparar_btn_pressed()
	await create_timer(_main.DURACION_GIRO + _main.DURACION_TENSION + 0.35).timeout
	await _captura("boom.png", marco)
	await create_timer(_main.PAUSA_FIN_PARTIDA + 1.4).timeout
	await _captura("final.png", marco)

	_main._on_menu_btn_pressed()
	_main._on_records_btn_pressed()
	await create_timer(0.6).timeout
	await _captura("records.png", marco)

	for r in ["user://shot_records.json", "user://shot_ajustes.json"]:
		if FileAccess.file_exists(r):
			DirAccess.remove_absolute(r)
	_main.free()
	await create_timer(0.3).timeout
	quit(0)
