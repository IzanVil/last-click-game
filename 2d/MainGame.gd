extends Control

const TAMANO_MIN := 6
const TAMANO_MAX := 20

var tamano_tambor : int
var posicion_bala : int

@onready var etiqueta_resultado : Label = $Centro/Columnas/Resultado
@onready var entrada_numero : LineEdit = $Centro/Columnas/EntradaNumero
@onready var etiqueta_instrucciones : Label = $Centro/Columnas/Instrucciones


func _ready() -> void:
	randomize()
	nueva_ronda()
	entrada_numero.text_submitted.connect(func(_texto): _on_disparar_btn_pressed())


func nueva_ronda() -> void:
	tamano_tambor = randi_range(TAMANO_MIN, TAMANO_MAX)
	posicion_bala = randi_range(1, tamano_tambor)
	etiqueta_instrucciones.text = "El tambor tiene una bala escondida entre 1 y " + str(tamano_tambor) + ". Escribe tu numero y dispara."
	etiqueta_resultado.text = "Escribe un numero del 1 al " + str(tamano_tambor) + " y pulsa Disparar..."
	entrada_numero.clear()
	entrada_numero.grab_focus()
	print("\n--- RULETA RUSA ---")
	print("Nueva ronda: bala entre 1 y ", tamano_tambor, ".")


func _on_disparar_btn_pressed() -> void:
	var numero : int = entrada_numero.text.to_int()
	if numero < 1 or numero > tamano_tambor:
		etiqueta_resultado.text = "Ese numero no esta en el tambor. Elige entre 1 y " + str(tamano_tambor) + "."
		entrada_numero.clear()
		entrada_numero.grab_focus()
		return

	if numero == posicion_bala:
		etiqueta_resultado.text = "BOOM. La bala estaba en " + str(posicion_bala) + ". Acertaste de lleno. Perdiste."
		print("💥 BOOM. La bala estaba en ", posicion_bala, ". Perdiste.")
		await get_tree().create_timer(1.5).timeout
		nueva_ronda()
	else:
		etiqueta_resultado.text = "Click. Solo un cartucho vacio. La bala estaba en " + str(posicion_bala) + " y tu elegiste " + str(numero) + ". Sobreviviste."
		print("👉 Click. La bala estaba en ", posicion_bala, ". Sobreviviste a la posicion ", numero, ".")
		await get_tree().create_timer(1.5).timeout
		nueva_ronda()

