class_name Eventos
extends RefCounted

const PROBABILIDAD := 0.25

const TIPOS_EVENTO: Array[String] = ["clic_metalico", "tambor_caliente"]

const TEXTOS := {
	"clic_metalico": "Se oye un clic metalico. El tambor se ha movido solo.",
	"tambor_caliente": "El tambor se calienta. Desconfia de la proxima pista.",
}


static func tirar_evento(
	probabilidad: float = PROBABILIDAD, rng: RandomNumberGenerator = null
) -> String:
	if Azar.flotante(rng) >= probabilidad:
		return ""
	return TIPOS_EVENTO[Azar.entero(rng, 0, TIPOS_EVENTO.size() - 1)]


static func texto_de(evento: String) -> String:
	assert(TEXTOS.has(evento), "Evento desconocido: %s" % evento)
	return TEXTOS[evento]
