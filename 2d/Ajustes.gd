class_name Ajustes
extends RefCounted
## Ajustes de accesibilidad, persistidos entre partidas.
##
## Hermano de Records.gd en forma (mismo JSON en `user://`, misma tolerancia
## a un archivo que no existe o esta corrupto) pero no en fondo: aqui no se
## guarda lo que el jugador ha hecho, sino como quiere ver y oir el juego.
##
## La version de terminal tiene su equivalente en las opciones de la CLI
## (`--sin-animaciones`, `--sin-sonido`): alli se eligen al arrancar y no se
## recuerdan, porque escribir el comando ya es la eleccion. Aqui no hay
## comando que escribir, asi que las casillas del menu se recuerdan solas.
##
## Ningun modulo de logica los consulta: los leen MainGame.gd y las vistas
## (TamborView, FondoTaller, Vineta) para decidir cuanto se mueve la pantalla,
## nunca que pasa en la partida.

const RUTA_POR_DEFECTO := "user://ajustes.json"

## Sin animaciones de adorno: ni engranajes girando, ni vibracion al morir,
## ni texto escribiendose letra a letra. Pensado para quien se marea con el
## movimiento, y de paso para maquinas modestas (con esto activado no se
## repinta nada por fotograma).
var efectos_reducidos := false

## Sube el cuerpo de la tipografia de toda la interfaz.
var texto_grande := false

## Paleta de mas contraste: los huecos del tambor y los textos pasan a
## colores mas claros y saturados, a costa de la penumbra noir.
var alto_contraste := false

## Efectos y musica. Es el equivalente de `--sin-sonido` en la version de
## terminal, al reves (aqui se guarda si SI suena) porque las casillas del
## menu se leen mejor en positivo.
var sonido := true

## Volumenes de las dos mezclas, de 0 a 1 (ver los buses "Musica" y
## "Efectos" que crea MainGame). Se guardan lineales, como los enseña el
## deslizador del menu de pausa, y se convierten a decibelios al aplicarlos.
var volumen_musica := 0.7
var volumen_efectos := 0.9

## Ventana o pantalla completa.
var pantalla_completa := false


## Carga los ajustes desde disco. Si el archivo no existe (primera partida)
## o esta corrupto, devuelve los de por defecto en vez de reventar.
static func cargar(ruta := RUTA_POR_DEFECTO) -> Ajustes:
	var archivo := FileAccess.open(ruta, FileAccess.READ)
	if archivo == null:
		return Ajustes.new()
	var texto := archivo.get_as_text()
	archivo.close()

	# JSON.new().parse() en vez de JSON.parse_string(), por lo mismo que en
	# Records.cargar(): un archivo corrupto es un caso previsto y no debe
	# ensuciar la salida con un "Parse JSON failed".
	var json := JSON.new()
	if json.parse(texto) != OK or not (json.data is Dictionary):
		return Ajustes.new()

	var ajustes := Ajustes.new()
	for campo in ajustes._campos():
		if not json.data.has(campo):
			continue
		# El tipo lo manda el valor por defecto del campo, no lo que venga
		# del archivo: un JSON a mano podria traer un 1 donde va un bool o
		# un entero donde va un volumen.
		if typeof(ajustes.get(campo)) == TYPE_BOOL:
			ajustes.set(campo, bool(json.data[campo]))
		else:
			ajustes.set(campo, clampf(float(json.data[campo]), 0.0, 1.0))
	return ajustes


## Guarda los ajustes en disco, creando la carpeta si hace falta.
## Devuelve true si se pudo escribir.
func guardar(ruta := RUTA_POR_DEFECTO) -> bool:
	var carpeta := ruta.get_base_dir()
	if not DirAccess.dir_exists_absolute(carpeta):
		DirAccess.make_dir_recursive_absolute(carpeta)

	var archivo := FileAccess.open(ruta, FileAccess.WRITE)
	if archivo == null:
		return false
	var datos := {}
	for campo in _campos():
		datos[campo] = get(campo)
	archivo.store_string(JSON.stringify(datos, "  "))
	archivo.close()
	return true


## Todos los campos que viajan al JSON. El tipo de cada uno lo dice su valor
## por defecto, y de eso se aprovecha cargar() para no tener que repetirlo.
func _campos() -> Array[String]:
	return [
		"efectos_reducidos",
		"texto_grande",
		"alto_contraste",
		"sonido",
		"volumen_musica",
		"volumen_efectos",
		"pantalla_completa",
	]
