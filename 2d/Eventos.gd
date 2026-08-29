class_name Eventos
extends RefCounted
## Eventos aleatorios tras un disparo fallido.
##
## Hermano de terminal/eventos.py. Tras sobrevivir un disparo real (no
## un farol), existe una probabilidad de que ocurra un evento que anade
## ruido a la deduccion del jugador. Estatico: no lleva estado propio.

const PROBABILIDAD := 0.25

const TIPOS_EVENTO: Array[String] = ["clic_metalico", "tambor_caliente"]

const TEXTOS := {
	"clic_metalico": "Se oye un clic metalico. El tambor se ha movido solo.",
	"tambor_caliente": "El tambor se calienta. Desconfia de la proxima pista.",
}


## Sortea si ocurre un evento. Devuelve su tipo, o "" si no pasa nada
## (GDScript no tiene None para String; "" hace ese papel aqui).
static func tirar_evento(probabilidad: float = PROBABILIDAD) -> String:
	if randf() >= probabilidad:
		return ""
	return TIPOS_EVENTO[randi() % TIPOS_EVENTO.size()]


## Devuelve el texto narrativo asociado a un tipo de evento.
static func texto_de(evento: String) -> String:
	assert(TEXTOS.has(evento), "Evento desconocido: %s" % evento)
	return TEXTOS[evento]
