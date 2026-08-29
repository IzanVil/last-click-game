class_name Historial
extends RefCounted
## Historial de una partida y su resumen narrativo.
##
## Hermano de terminal/historial.py. No es una pantalla ni una regla del
## juego: solo lleva la cuenta de lo que ha ido pasando (faroles,
## eventos) para poder resumirlo en una frase al terminar la partida,
## gane o pierda el jugador.

var faroles_usados := 0
var faroles_acertados := 0
var eventos: Dictionary = {}


## Anota un uso de farol, acertado o no.
func registrar_farol(acierto: bool) -> void:
	faroles_usados += 1
	if acierto:
		faroles_acertados += 1


## Anota que ha ocurrido un evento aleatorio de tipo `tipo`.
func registrar_evento(tipo: String) -> void:
	eventos[tipo] = eventos.get(tipo, 0) + 1


## Genera la frase narrativa final para `dias` dias sobrevividos.
func resumen(dias: int) -> String:
	var dia_txt := "dia" if dias == 1 else "dias"
	var partes: Array[String] = ["sobreviviste %d %s" % [dias, dia_txt]]

	if faroles_usados > 0:
		var vez_txt := "vez" if faroles_usados == 1 else "veces"
		var acierto_txt := "acertado" if faroles_acertados == 1 else "acertados"
		partes.append(
			"faroleaste %d %s (%d %s)" % [faroles_usados, vez_txt, faroles_acertados, acierto_txt]
		)

	var total_eventos := 0
	for cantidad: int in eventos.values():
		total_eventos += cantidad
	if total_eventos > 0:
		var evento_txt := "evento" if total_eventos == 1 else "eventos"
		partes.append("viviste %d %s del tambor" % [total_eventos, evento_txt])

	if partes.size() == 1:
		return "Hoy %s, sin faroles ni sobresaltos." % partes[0]
	return "Hoy " + ", ".join(partes.slice(0, -1)) + " y " + partes[-1] + "."
