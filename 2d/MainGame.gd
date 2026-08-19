extends Control

const HUECOS := 10
const RONDAS := 8
const BALAS_POR_RONDA := [1, 2, 3, 4, 5, 6, 7, 8]

var ronda_actual := 1
var posiciones_bala : Array          # posiciones (del 1 al 10) que tienen bala
@onready var etiqueta_resultado : Label = $Centro/Columnas/Resultado
@onready var etiqueta_instrucciones : Label = $Centro/Columnas/Instrucciones
@onready var entrada_numero : LineEdit = $Centro/Columnas/EntradaNumero


func _ready() -> void:
	randomize()
	iniciar_juego()
	entrada_numero.text_submitted.connect(func(_texto): _on_disparar_btn_pressed())


func iniciar_juego() -> void:
	ronda_actual = 1
	preparar_ronda()


func preparar_ronda() -> void:
	var num_balas : int = BALAS_POR_RONDA[ronda_actual - 1]
	posiciones_bala = _colocar_balas(num_balas)
	actualizar_pantalla()


func _colocar_balas(cantidad: int) -> Array:
	var posiciones := []
	while posiciones.size() < cantidad:
		var p : int = randi_range(1, HUECOS)
		if not posiciones.has(p):
			posiciones.append(p)
	return posiciones


func actualizar_pantalla() -> void:
	var num_balas : int = BALAS_POR_RONDA[ronda_actual - 1]
	var num_vacios : int = HUECOS - num_balas
	etiqueta_instrucciones.text = "Ronda " + str(ronda_actual) + " de " + str(RONDAS) + " - Tambor de " + str(HUECOS) + " huecos: " + str(num_balas) + " balas y " + str(num_vacios) + " vacios."
	etiqueta_resultado.text = "Elige un numero del 1 al 10 y dispara..."
	entrada_numero.clear()
	entrada_numero.grab_focus()
	print("\n--- RULETA RUSA - Ronda ", ronda_actual, "/", RONDAS, " ---")
	print("Balas: ", posiciones_bala, " / Vacios: 1-", HUECOS, " menos las balas.")
func _on_disparar_btn_pressed() -> void:
	var numero : int = entrada_numero.text.to_int()
	if numero < 1 or numero > HUECOS:
		etiqueta_resultado.text = "Ese numero no esta en el tambor. Elige entre 1 y " + str(HUECOS) + "."
		entrada_numero.clear()
		entrada_numero.grab_focus()
		return

	if numero in posiciones_bala:
		etiqueta_resultado.text = "BOOM. La posicion " + str(numero) + " tenia una bala. Perdiste en la ronda " + str(ronda_actual) + "."
		print("💥 BOOM. Perdiste en la ronda ", ronda_actual, ". Bala en ", numero, ".")
		await get_tree().create_timer(2.0).timeout
		iniciar_juego()
	else:
		etiqueta_resultado.text = "Click. La posicion " + str(numero) + " estaba vacia. Sobreviviste a la ronda " + str(ronda_actual) + "."
		print("👉 Click. Sobreviviste a la ronda ", ronda_actual, ".")
		if ronda_actual >= RONDAS:
			etiqueta_resultado.text = "🏆 Sobreviviste las " + str(RONDAS) + " rondas. ERES UNA LEYENDA."
			print("🏆 Sobreviviste las ", RONDAS, " rondas. Eres una leyenda.")
			await get_tree().create_timer(2.5).timeout
			iniciar_juego()
		else:
			ronda_actual += 1
			await get_tree().create_timer(1.8).timeout
			preparar_ronda()

