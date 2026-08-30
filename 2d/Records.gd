class_name Records
extends RefCounted
## Records y estadisticas persistidos entre partidas.
##
## Hermano de terminal/records.py. La version de terminal guarda en
## ~/.tambor_del_juicio/records.json; aqui se usa `user://records.json`,
## que es el equivalente idiomatico en Godot (y el unico sitio donde un
## juego exportado tiene permiso de escritura garantizado en las tres
## plataformas). Los contadores y el formato del JSON son los mismos.

const RUTA_POR_DEFECTO := "user://records.json"

var partidas_jugadas := 0
var dias_maximos := 0
var puntos_maximos := 0
var faroles_usados := 0
var faroles_acertados := 0


## Actualiza los contadores tras una partida (gane o pierda).
func registrar_partida(
	dias: int, puntos: int, p_faroles_usados: int, p_faroles_acertados: int
) -> void:
	partidas_jugadas += 1
	dias_maximos = maxi(dias_maximos, dias)
	puntos_maximos = maxi(puntos_maximos, puntos)
	faroles_usados += p_faroles_usados
	faroles_acertados += p_faroles_acertados


## Carga los records desde disco.
##
## Si el archivo no existe todavia (primera partida) o esta corrupto,
## devuelve unos records vacios en vez de reventar: un fichero de records
## roto no deberia impedir jugar.
static func cargar(ruta := RUTA_POR_DEFECTO) -> Records:
	var archivo := FileAccess.open(ruta, FileAccess.READ)
	if archivo == null:
		return Records.new()
	var texto := archivo.get_as_text()
	archivo.close()

	# JSON.new().parse() en vez de JSON.parse_string(): con un texto
	# invalido, parse_string() ademas de devolver null imprime un
	# "ERROR: Parse JSON failed" en el log. Aqui un archivo corrupto es
	# un caso previsto, no un fallo que merezca ensuciar la salida.
	var json := JSON.new()
	if json.parse(texto) != OK or not (json.data is Dictionary):
		return Records.new()

	var records := Records.new()
	for campo in records._campos():
		if json.data.has(campo):
			# Los numeros de un JSON vuelven siempre como float en Godot,
			# aunque se guardasen como enteros. Los campos de abajo estan
			# tipados como int, asi que set() ya haria la conversion solo;
			# el int() explicito deja constancia de la conversion y la
			# mantiene si algun dia esos campos pierden el tipo estatico.
			records.set(campo, int(json.data[campo]))
	return records


## Guarda los records en disco, creando la carpeta si hace falta.
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


## Frase resumen de los records, para mostrar en pantalla.
func resumen() -> String:
	if partidas_jugadas == 0:
		return "Todavia no hay recuerdos del tambor: esta sera tu primera partida."

	var porcentaje := 0.0
	if faroles_usados > 0:
		porcentaje = 100.0 * faroles_acertados / faroles_usados
	return (
		"Record: %d dia(s) sobrevividos y %d puntos en una sola partida, en %d partida(s) jugada(s). "
		% [dias_maximos, puntos_maximos, partidas_jugadas]
		+ "Faroles acertados: %d/%d (%.0f%%)." % [faroles_acertados, faroles_usados, porcentaje]
	)


func _campos() -> Array[String]:
	return [
		"partidas_jugadas",
		"dias_maximos",
		"puntos_maximos",
		"faroles_usados",
		"faroles_acertados",
	]
