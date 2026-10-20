class_name TamborJuicio
extends RefCounted

const PATRONES: Array[String] = ["avanza", "retrocede", "salta_dos", "espejo"]

const DISPAROS_POR_DIA := 3


static func dias_sobrevividos(
	disparos_superados: int, disparos_por_dia: int = DISPAROS_POR_DIA
) -> int:
	return disparos_superados / disparos_por_dia


var huecos: int
var patron: String
var posicion_bala: int
var ultimo_disparo := -1
var historial: Array[int] = []


func _init(
	p_huecos: int,
	p_patron: String = "",
	p_posicion_inicial: int = -1,
	p_rng: RandomNumberGenerator = null,
) -> void:
	assert(p_huecos >= 2, "El tambor necesita al menos 2 huecos.")
	assert(
		p_patron == "" or PATRONES.has(p_patron), "Patron de movimiento desconocido: %s" % p_patron
	)
	assert(
		p_posicion_inicial == -1 or (p_posicion_inicial >= 1 and p_posicion_inicial <= p_huecos),
		"Posicion inicial fuera de rango: %d" % p_posicion_inicial
	)

	huecos = p_huecos
	patron = p_patron if p_patron != "" else PATRONES[Azar.entero(p_rng, 0, PATRONES.size() - 1)]
	posicion_bala = (
		p_posicion_inicial if p_posicion_inicial != -1 else Azar.entero(p_rng, 1, huecos)
	)


func disparar(numero: int) -> bool:
	assert(numero >= 1 and numero <= huecos, "Posicion fuera de rango: %d" % numero)

	ultimo_disparo = numero
	historial.append(numero)

	var impacto := numero == posicion_bala
	if not impacto:
		posicion_bala = _mover(posicion_bala, patron, huecos)
	return impacto


func mover_extra() -> int:
	posicion_bala = _mover(posicion_bala, patron, huecos)
	return posicion_bala


static func _mover(posicion: int, patron: String, huecos: int) -> int:
	match patron:
		"avanza":
			return posicion % huecos + 1
		"retrocede":
			return (posicion - 2 + huecos) % huecos + 1
		"salta_dos":
			return (posicion + 1) % huecos + 1
		"espejo":
			return huecos + 1 - posicion
		_:
			push_error("Patron de movimiento desconocido: %s" % patron)
			return posicion
