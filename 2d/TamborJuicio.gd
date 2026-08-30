class_name TamborJuicio
extends RefCounted
## Tambor con una unica bala que se desplaza tras cada disparo fallido.
##
## Hermano de terminal/estado.py (TamborJuicio): misma logica, mismo
## vocabulario. No conoce nodos ni UI. "Fallido" se entiende desde la
## bala: un disparo que no la encuentra. El patron de movimiento se
## sortea al construir el tambor y no cambia durante la partida.

const PATRONES: Array[String] = ["avanza", "retrocede", "salta_dos", "espejo"]

## Cuantos disparos sobrevividos forman un "dia de vida". Vive aqui, y no
## en RuletaEstado, para que sea espejo exacto de terminal/estado.py, que
## declara DISPAROS_POR_DIA y dias_sobrevividos() junto a TamborJuicio.
const DISPAROS_POR_DIA := 3


## Cuenta cuantos dias completos (de `disparos_por_dia` disparos) se han
## sobrevivido. Un dia en curso, aun sin terminar, no cuenta todavia.
static func dias_sobrevividos(
	disparos_superados: int, disparos_por_dia: int = DISPAROS_POR_DIA
) -> int:
	return disparos_superados / disparos_por_dia

var huecos: int
var patron: String
var posicion_bala: int
## -1 significa "todavia no ha habido ningun disparo" (GDScript no tiene
## None para int; es el mismo papel que None en la version Python).
var ultimo_disparo := -1
var historial: Array[int] = []


## `p_patron == ""` sortea uno de PATRONES; `p_posicion_inicial == -1`
## sortea la posicion de la bala. Ambos son los valores por defecto.
func _init(p_huecos: int, p_patron: String = "", p_posicion_inicial: int = -1) -> void:
	assert(p_huecos >= 2, "El tambor necesita al menos 2 huecos.")
	assert(p_patron == "" or PATRONES.has(p_patron), "Patron de movimiento desconocido: %s" % p_patron)
	assert(p_posicion_inicial == -1 or (p_posicion_inicial >= 1 and p_posicion_inicial <= p_huecos),
		"Posicion inicial fuera de rango: %d" % p_posicion_inicial)

	huecos = p_huecos
	patron = p_patron if p_patron != "" else PATRONES[randi() % PATRONES.size()]
	posicion_bala = p_posicion_inicial if p_posicion_inicial != -1 else randi_range(1, huecos)


## Resuelve un disparo a `numero`. Devuelve true si impacta en la bala.
## Si no impacta, la bala se desplaza segun `patron` antes de devolver
## el control: la siguiente pista y el siguiente disparo ya veran la
## posicion nueva.
func disparar(numero: int) -> bool:
	assert(numero >= 1 and numero <= huecos, "Posicion fuera de rango: %d" % numero)

	ultimo_disparo = numero
	historial.append(numero)

	var impacto := numero == posicion_bala
	if not impacto:
		posicion_bala = _mover(posicion_bala, patron, huecos)
	return impacto


## Desplaza la bala una vez mas, fuera de un disparo. Lo dispara un
## evento aleatorio (ver Eventos.gd) para simular que el tambor se ha
## movido solo entre disparo y disparo.
func mover_extra() -> int:
	posicion_bala = _mover(posicion_bala, patron, huecos)
	return posicion_bala


static func _mover(posicion: int, patron: String, huecos: int) -> int:
	match patron:
		"avanza":
			return posicion % huecos + 1
		"retrocede":
			# GDScript, a diferencia de Python, no garantiza un resultado
			# no negativo en el modulo de un numero negativo: sumar
			# `huecos` antes de aplicarlo evita ese caso.
			return (posicion - 2 + huecos) % huecos + 1
		"salta_dos":
			return (posicion + 1) % huecos + 1
		"espejo":
			return huecos + 1 - posicion
		_:
			push_error("Patron de movimiento desconocido: %s" % patron)
			return posicion
