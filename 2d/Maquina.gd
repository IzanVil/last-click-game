class_name Maquina
extends RefCounted
## Efecto de maquina de escribir para las etiquetas de texto.
##
## Hermano de la escritura letra a letra de la version de terminal: alli se
## imprime caracter a caracter con pausas; aqui se pone el texto entero de
## golpe y se revela con `visible_ratio`, que es lo que Godot ofrece para
## esto y ademas deja `text` completo desde el primer fotograma (util para
## los tests, que leen `.text` sin esperar a la animacion).
##
## Todo estatico: no lleva estado propio. El Tween en curso se guarda en un
## meta de la propia etiqueta para poder cancelarlo si llega un texto nuevo
## antes de terminar el anterior; asi dos mensajes seguidos no se pisan.

const META_TWEEN := "tween_maquina"

## Velocidad de tecleo. Lo bastante rapida para no desesperar leyendo, lo
## bastante lenta para que se note el golpe de tecla.
const CARACTERES_POR_SEGUNDO := 55.0


## Escribe `texto` en `etiqueta` letra a letra a partir del caracter
## `desde` (lo anterior se da por escrito y aparece ya entero: sirve para
## añadir una linea a un mensaje sin reescribir lo que ya se leia).
##
## Con `cps <= 0` el texto sale de golpe, que es lo que hace falta con los
## efectos reducidos (ver Ajustes.efectos_reducidos) y en los tests.
static func escribir(
	etiqueta: Label, texto: String, desde: int = 0, cps: float = CARACTERES_POR_SEGUNDO
) -> void:
	_cancelar(etiqueta)
	etiqueta.text = texto

	var pendientes := texto.length() - desde
	if cps <= 0.0 or pendientes <= 0:
		etiqueta.visible_ratio = 1.0
		return

	etiqueta.visible_ratio = float(desde) / texto.length()
	var tween := etiqueta.create_tween()
	tween.tween_property(etiqueta, "visible_ratio", 1.0, pendientes / cps)
	etiqueta.set_meta(META_TWEEN, tween)


## Deja a la vista todo el texto de `etiqueta`, cortando el tecleo si
## estaba en marcha. Se usa al cambiar de pantalla: un mensaje a medio
## escribir no debe seguir apareciendo debajo del siguiente.
static func completar(etiqueta: Label) -> void:
	_cancelar(etiqueta)
	etiqueta.visible_ratio = 1.0


static func _cancelar(etiqueta: Label) -> void:
	if not etiqueta.has_meta(META_TWEEN):
		return
	var tween: Tween = etiqueta.get_meta(META_TWEEN)
	if tween != null and tween.is_valid():
		tween.kill()
	etiqueta.remove_meta(META_TWEEN)
