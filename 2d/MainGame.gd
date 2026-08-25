extends Control
## Vista de la ruleta rusa: solo escucha las senales de RuletaEstado y
## actualiza Label/ColorRect/Tween en pantalla. No conoce reglas del
## juego (rondas, balas, condicion de victoria viven en RuletaEstado).

const COLOR_NORMAL := Color(0.15, 0.15, 0.2, 1)
const COLOR_BOOM := Color(0.45, 0.05, 0.05, 1)
const COLOR_CLICK := Color(0.05, 0.3, 0.1, 1)
const COLOR_VICTORIA := Color(0.25, 0.2, 0.05, 1)

@onready var fondo: ColorRect = $Fondo
@onready var etiqueta_resultado: Label = $Centro/Columnas/Resultado
@onready var etiqueta_instrucciones: Label = $Centro/Columnas/Instrucciones
@onready var entrada_numero: LineEdit = $Centro/Columnas/EntradaNumero
@onready var disparar_btn: Button = $Centro/Columnas/DispararBtn
@onready var tambor: TamborView = $Centro/Columnas/Tambor
@onready var sonido_disparo: AudioStreamPlayer = $SonidoDisparo
@onready var sonido_victoria: AudioStreamPlayer = $SonidoVictoria
@onready var sonido_derrota: AudioStreamPlayer = $SonidoDerrota

const RuletaEstado := preload("res://RuletaEstado.gd")

var _estado := RuletaEstado.new()

## Evita disparos dobles mientras tambor.tension() esta en marcha: el
## resultado ya esta decidido, pero la vista aun no lo ha revelado.
var _disparo_bloqueado := false


func _ready() -> void:
	randomize()
	_estado.ronda_preparada.connect(_on_ronda_preparada)
	_estado.entrada_invalida.connect(_on_entrada_invalida)
	_estado.impacto.connect(_on_impacto)
	_estado.click_seguro.connect(_on_click_seguro)
	_estado.partida_ganada.connect(_on_partida_ganada)
	entrada_numero.text_submitted.connect(func(_texto): _on_disparar_btn_pressed())
	_estado.iniciar_juego()


func _on_disparar_btn_pressed() -> void:
	if _disparo_bloqueado:
		return

	var numero: int = entrada_numero.text.to_int()
	if numero < 1 or numero > RuletaEstado.HUECOS:
		_estado.disparar(numero)  # deja que RuletaEstado emita entrada_invalida
		return

	_disparo_bloqueado = true
	entrada_numero.editable = false
	disparar_btn.disabled = true
	etiqueta_resultado.text = "..."
	await tambor.tension(numero)
	_estado.disparar(numero)


func _on_ronda_preparada(ronda: int, balas: int, vacios: int) -> void:
	etiqueta_instrucciones.text = (
		"Ronda " + str(ronda) + " de " + str(RuletaEstado.RONDAS)
		+ " - Tambor de " + str(RuletaEstado.HUECOS) + " huecos: "
		+ str(balas) + " balas y " + str(vacios) + " vacios."
	)
	etiqueta_resultado.text = "Elige un numero del 1 al 10 y dispara..."
	_disparo_bloqueado = false
	entrada_numero.editable = true
	disparar_btn.disabled = false
	entrada_numero.clear()
	entrada_numero.grab_focus()
	tambor.preparar_ronda(RuletaEstado.HUECOS)
	tambor.girar()
	print("\n--- RULETA RUSA - Ronda ", ronda, "/", RuletaEstado.RONDAS, " ---")
	print("Balas: ", _estado.posiciones_bala, " / Vacios: 1-", RuletaEstado.HUECOS, " menos las balas.")


func _on_entrada_invalida(_numero: int) -> void:
	etiqueta_resultado.text = (
		"Ese numero no esta en el tambor. Elige entre 1 y " + str(RuletaEstado.HUECOS) + "."
	)
	entrada_numero.clear()
	entrada_numero.grab_focus()


func _on_impacto(ronda: int, numero: int) -> void:
	etiqueta_resultado.text = (
		"BOOM. La posicion " + str(numero) + " tenia una bala. Perdiste en la ronda "
		+ str(ronda) + "."
	)
	print("💥 BOOM. Perdiste en la ronda ", ronda, ". Bala en ", numero, ".")
	tambor.revelar(numero, true)
	sonido_disparo.play()
	sonido_derrota.play()
	_flash(COLOR_BOOM)
	await get_tree().create_timer(2.0).timeout
	_estado.iniciar_juego()


func _on_click_seguro(ronda: int, numero: int) -> void:
	etiqueta_resultado.text = (
		"Click. La posicion " + str(numero) + " estaba vacia. Sobreviviste a la ronda "
		+ str(ronda) + "."
	)
	print("👉 Click. Sobreviviste a la ronda ", ronda, ".")
	tambor.revelar(numero, false)
	sonido_disparo.play()
	if ronda < RuletaEstado.RONDAS:
		_flash(COLOR_CLICK)
		await get_tree().create_timer(1.8).timeout
		_estado.avanzar_ronda()
	# Si ronda == RONDAS, _on_partida_ganada ya se dispara justo despues
	# (disparar() emite click_seguro y partida_ganada en el mismo turno)
	# y se encarga del mensaje, el flash y el reinicio.


func _on_partida_ganada(rondas: int) -> void:
	etiqueta_resultado.text = "🏆 Sobreviviste las " + str(rondas) + " rondas. ERES UNA LEYENDA."
	print("🏆 Sobreviviste las ", rondas, " rondas. Eres una leyenda.")
	sonido_victoria.play()
	_flash(COLOR_VICTORIA)
	await get_tree().create_timer(2.5).timeout
	_estado.iniciar_juego()


func _flash(color: Color) -> void:
	var tween := create_tween()
	tween.tween_property(fondo, "color", color, 0.15)
	tween.tween_property(fondo, "color", COLOR_NORMAL, 0.6)
