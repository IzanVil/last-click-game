extends RefCounted
## Estado y logica pura del juego de ruleta rusa (sin nodos ni UI).
##
## No conoce Label, ColorRect ni Tween: solo lleva la ronda actual y las
## balas del tambor, y emite senales cuando pasa algo relevante. La vista
## (MainGame.gd) se conecta a esas senales y decide como mostrarlas.
##
## Las reglas son las mismas que en la version de terminal
## (terminal/ruleta.py): tambor de HUECOS huecos, RONDAS rondas y una bala
## mas en cada ronda.

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

const HUECOS := 10
const RONDAS := 8

var ronda_actual := 1
var posiciones_bala: Array[int] = []


## Comprueba que `huecos`/`rondas` son una combinacion jugable, con el
## mismo criterio que _validar_dificultad() en terminal/ruleta.py.
##
## GDScript no tiene excepciones, asi que en vez de lanzar ValueError se
## avisa por push_error() (sale en consola y en el log de la CI) y se
## devuelve false, para que quien llame pueda abortar en vez de arrancar
## una partida imposible. Es static y toma parametros --en vez de mirar
## HUECOS/RONDAS directamente-- para poder probarla con combinaciones
## invalidas sin tocar las constantes.
static func validar_dificultad(huecos: int, rondas: int) -> bool:
	if huecos < 1:
		push_error("huecos debe ser al menos 1 (recibido: %d)." % huecos)
		return false
	if rondas < 1:
		push_error("rondas debe ser al menos 1 (recibido: %d)." % rondas)
		return false
	if rondas > huecos:
		var motivo := "necesitaria mas balas de las que caben en el tambor."
		push_error(
			(
				"rondas (%d) no puede ser mayor que huecos (%d): la ultima ronda %s"
				% [rondas, huecos, motivo]
			)
		)
		return false
	return true


## Unico sitio donde vive la regla "que numeros acepta el tambor". La
## vista la consulta para decidir si merece la pena animar el disparo,
## en vez de repetir el rango 1..HUECOS por su cuenta.
static func es_numero_valido(numero: int) -> bool:
	return numero >= 1 and numero <= HUECOS


## Arranca una partida desde la ronda 1. Devuelve false (sin emitir nada)
## si HUECOS/RONDAS no forman una dificultad jugable: eso solo puede pasar
## editando mal las constantes, asi que ademas del push_error() de
## validar_dificultad() se corta con assert() para que reviente de forma
## visible en el editor en vez de dejar una partida a medias.
func iniciar_juego() -> bool:
	if not validar_dificultad(HUECOS, RONDAS):
		assert(false, "Dificultad no jugable: revisa HUECOS/RONDAS.")
		return false

	ronda_actual = 1
	preparar_ronda()
	return true


func preparar_ronda() -> void:
	# La ronda N lleva N balas (ronda 1 -> 1 bala ... ronda RONDAS ->
	# RONDAS balas), igual que en terminal/ruleta.py. Antes esto era una
	# tabla constante BALAS_POR_RONDA = [1, 2, ..., 8] que habia que
	# mantener sincronizada a mano con RONDAS: subir RONDAS sin alargar la
	# tabla reventaba con un index out of range a mitad de partida.
	var num_balas := ronda_actual
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
	if not es_numero_valido(numero):
		entrada_invalida.emit(numero)
		return

	if numero in posiciones_bala:
		impacto.emit(ronda_actual, numero)
		return

	click_seguro.emit(ronda_actual, numero)
	if ronda_actual >= RONDAS:
		partida_ganada.emit(RONDAS)


## Reparte `cantidad` balas en huecos distintos del tambor.
##
## Baraja los huecos y se queda con los primeros `cantidad`, en vez del
## bucle anterior (sortear un hueco al azar y reintentar si ya estaba
## cogido): aquel nunca terminaba si cantidad > HUECOS, colgando el juego
## en un bucle infinito en vez de fallar. Es el mismo arreglo que ya se
## hizo en terminal/ruleta.py al pasar a random.sample(). El clamp es una
## red de seguridad: validar_dificultad() ya garantiza que no se llegue
## aqui pidiendo mas balas de las que caben.
func _colocar_balas(cantidad: int) -> Array[int]:
	var huecos: Array[int] = []
	for hueco in range(1, HUECOS + 1):
		huecos.append(hueco)
	huecos.shuffle()
	return huecos.slice(0, clampi(cantidad, 0, HUECOS))
