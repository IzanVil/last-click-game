extends Control

var posicion_bala : int
var ronda_actual : int = 1

@onready var etiqueta_resultado : Label = $Centro/Columnas/Resultado


func _ready() -> void:
	randomize()
	posicion_bala = randi_range(1, 6)
	etiqueta_resultado.text = "Pulsa Disparar o deja que la suerte decida..."
	print("\n--- RUELETA RUSA INICIADA ---")
	print("Bala en posicion ", posicion_bala, ". Pulsa ESPACIO o el boton para disparar.")


func _process(_delta: float) -> void:
	if Input.is_action_just_pressed("ui_accept"):
		disparar()
func _on_disparar_btn_pressed() -> void:
	disparar()


func disparar() -> void:
	if ronda_actual == posicion_bala:
		etiqueta_resultado.text = "BOOM. La bala estaba en " + str(posicion_bala) + ". Perdiste en la ronda " + str(ronda_actual) + ". El tambor gira de nuevo."
		print("💥 BOOM en la posicion ", posicion_bala, ". Moriste en la ronda ", ronda_actual, ".")
		ronda_actual = 1
		_ready()
	else:
		etiqueta_resultado.text = "Click. Cartucho vacio. Sobreviviste a la ronda " + str(ronda_actual) + ". Continua."
		print("👉 Click. Sobrevives a la ronda ", ronda_actual, ".")
		ronda_actual += 1
		if ronda_actual > 6:
			etiqueta_resultado.text = "HAS SOBREVIVIDO TODAS LAS RONDAS. ERES UNA LEYENDA."
			print("🏆 Sobreviviste las 6 rondas. Eres una leyenda.")
			ronda_actual = 1
			_ready()
