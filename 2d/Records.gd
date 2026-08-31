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

## Cuantas partidas se guardan en la tabla de mejores marcas.
const MAX_MEJORES := 5

var partidas_jugadas := 0
var dias_maximos := 0
var puntos_maximos := 0
var faroles_usados := 0
var faroles_acertados := 0

## Las MAX_MEJORES mejores partidas, de la mejor a la peor: diccionarios
## con "dias", "puntos" y "fecha" (AAAA-MM-DD).
##
## Es lo unico que este modulo tiene y su hermano terminal/records.py no:
## alli los records se leen de una linea de texto al arrancar, y aqui hay
## una pantalla entera para enseñarlos. El resto de campos son los mismos y
## el JSON sigue siendo compatible en los dos sentidos (cada version ignora
## las claves que no conoce).
var mejores: Array[Dictionary] = []


## Actualiza los contadores tras una partida (gane o pierda) y la mete en la
## tabla de mejores marcas si da la talla.
func registrar_partida(
	dias: int, puntos: int, p_faroles_usados: int, p_faroles_acertados: int
) -> void:
	partidas_jugadas += 1
	dias_maximos = maxi(dias_maximos, dias)
	puntos_maximos = maxi(puntos_maximos, puntos)
	faroles_usados += p_faroles_usados
	faroles_acertados += p_faroles_acertados
	_anotar_en_mejores(dias, puntos)


## Mete la partida en la tabla y se queda con las MAX_MEJORES primeras.
## Ordena por dias sobrevividos y, a igualdad, por puntos: el mismo
## criterio con el que se decide quien gana un duelo (ver Jugador.ganadores).
func _anotar_en_mejores(dias: int, puntos: int) -> void:
	var fecha := Time.get_date_dict_from_system()
	mejores.append({
		"dias": dias,
		"puntos": puntos,
		"fecha": "%04d-%02d-%02d" % [fecha["year"], fecha["month"], fecha["day"]],
	})
	mejores.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		if a["dias"] != b["dias"]:
			return a["dias"] > b["dias"]
		return a["puntos"] > b["puntos"]
	)
	if mejores.size() > MAX_MEJORES:
		mejores.resize(MAX_MEJORES)


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
	if json.data.get("mejores") is Array:
		for entrada in json.data["mejores"]:
			if entrada is Dictionary and entrada.has("dias") and entrada.has("puntos"):
				records.mejores.append({
					"dias": int(entrada["dias"]),
					"puntos": int(entrada["puntos"]),
					"fecha": str(entrada.get("fecha", "")),
				})
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
	datos["mejores"] = mejores
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


## Los campos enteros que viajan al JSON, en el orden en que se escriben.
## `mejores` no esta aqui porque no es un entero: se guarda y se recarga
## aparte (ver guardar y cargar).
func _campos() -> Array[String]:
	return [
		"partidas_jugadas",
		"dias_maximos",
		"puntos_maximos",
		"faroles_usados",
		"faroles_acertados",
	]
