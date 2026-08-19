extends Control

var posicion_bala : int

@onready var etiqueta_resultado : Label = $Centro/Columnas/Resultado
@onready var entrada_numero : LineEdit = $Centro/Columnas/EntradaNumero
func _ready() -> void:
	randomize()
	posicion_bala = randi_range(1, 6)
	etiqueta_resultado.text = "Escribe tu numero del 1 al 6 y pulsa Disparar..."
	entrada_numero.clear()
	entrada_numero.grab_focus()
	entrada_numero.text_submitted.connect(func(_texto): _on_disparar_btn_pressed())
func _on_disparar_btn_pressed() -> void:
	var numero : int = entrada_numero.text.to_int()
	if numero < 1 or numero > 6:
		etiqueta_resultado.text = "Ese numero no esta en el tambor. Escribe un numero del 1 al 6."
		return

	if numero == posicion_bala:
		etiqueta_resultado.text = "BOOM. La bala estaba en " + str(posicion_bala) + ". Acertaste de lleno. Perdiste."
		print("💥 BOOM. La bala estaba en ", posicion_bala, ". Perdiste.")
	else:
		etiqueta_resultado.text = "Click. Solo un cartucho vacio. Sobreviviste a la posicion " + str(numero) + "."
		print("👉 Click. Sobreviviste a la posicion ", numero, ".")

	entrada_numero.text = ""
	entrada_numero.grab_focus()
