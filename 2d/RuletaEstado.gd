extends RefCounted
## Estado y logica pura del juego de ruleta rusa (sin nodos ni UI).
##
## No conoce Label, ColorRect ni Tween: solo lleva la ronda actual y las
## balas del tambor, y emite senales cuando pasa algo relevante. La vista
## (MainGame.gd) se conecta a esas senales y decide como mostrarlas.

const HUECOS := 10
const RONDAS := 8
const BALAS_POR_RONDA := [1, 2, 3, 4, 5, 6, 7, 8]

## Se emite al preparar una ronda nueva, con las balas ya colocadas.
signal ronda_preparada(ronda: int, balas: int, vacios: int)
## Se emite cuando el numero elegido no esta entre 1 y HUECOS.
signal entrada_invalida(numero: int)
## Se emite cuando el disparo impacta en una bala.
signal impacto(ronda: int, numero: int)
## Se emite cuando el disparo cae en un hueco vacio.
signal click_seguro(ronda: int, numero: int)
## Se emite al sobrevivir la ultima ronda.
signal partida_ganada(rondas: int)

var ronda_actual := 1
var posiciones_bala: Array = []


func iniciar_juego() -> void:
	ronda_actual = 1
	preparar_ronda()


func preparar_ronda() -> void:
	var num_balas: int = BALAS_POR_RONDA[ronda_actual - 1]
	posiciones_bala = _colocar_balas(num_balas)
	ronda_preparada.emit(ronda_actual, num_balas, HUECOS - num_balas)


## Avanza a la siguiente ronda y la prepara. Lo llama la vista cuando ya
## termino de mostrar el resultado de la ronda anterior (tras su propia
## pausa/animacion), no se dispara solo desde disparar().
func avanzar_ronda() -> void:
	ronda_actual += 1
	preparar_ronda()


## Resuelve un disparo a `numero` y emite la senal que corresponda.
## No decide temporizaciones ni avanza de ronda por si solo (ver
## avanzar_ronda): eso queda en manos de quien escuche las senales.
func disparar(numero: int) -> void:
	if numero < 1 or numero > HUECOS:
		entrada_invalida.emit(numero)
		return

	if numero in posiciones_bala:
		impacto.emit(ronda_actual, numero)
		return

	click_seguro.emit(ronda_actual, numero)
	if ronda_actual >= RONDAS:
		partida_ganada.emit(RONDAS)


func _colocar_balas(cantidad: int) -> Array:
	var posiciones := []
	while posiciones.size() < cantidad:
		var p: int = randi_range(1, HUECOS)
		if not posiciones.has(p):
			posiciones.append(p)
	return posiciones
