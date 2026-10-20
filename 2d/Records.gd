class_name Records
extends RefCounted

const RUTA_POR_DEFECTO := "user://records.json"

const MAX_MEJORES := 5

var partidas_jugadas := 0
var dias_maximos := 0
var puntos_maximos := 0
var faroles_usados := 0
var faroles_acertados := 0

var mejores: Array[Dictionary] = []


func registrar_partida(
	dias: int, puntos: int, p_faroles_usados: int, p_faroles_acertados: int
) -> void:
	partidas_jugadas += 1
	dias_maximos = maxi(dias_maximos, dias)
	puntos_maximos = maxi(puntos_maximos, puntos)
	faroles_usados += p_faroles_usados
	faroles_acertados += p_faroles_acertados
	_anotar_en_mejores(dias, puntos)


func _anotar_en_mejores(dias: int, puntos: int) -> void:
	var fecha := Time.get_date_dict_from_system()
	var fecha_texto := "%04d-%02d-%02d" % [fecha["year"], fecha["month"], fecha["day"]]
	mejores.append({"dias": dias, "puntos": puntos, "fecha": fecha_texto})
	mejores.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			if a["dias"] != b["dias"]:
				return a["dias"] > b["dias"]
			return a["puntos"] > b["puntos"]
	)
	if mejores.size() > MAX_MEJORES:
		mejores.resize(MAX_MEJORES)


static func cargar(ruta := RUTA_POR_DEFECTO) -> Records:
	var archivo := FileAccess.open(ruta, FileAccess.READ)
	if archivo == null:
		return Records.new()
	var texto := archivo.get_as_text()
	archivo.close()

	var json := JSON.new()
	if json.parse(texto) != OK or not (json.data is Dictionary):
		return Records.new()

	var records := Records.new()
	if json.data.get("mejores") is Array:
		for entrada in json.data["mejores"]:
			if entrada is Dictionary and entrada.has("dias") and entrada.has("puntos"):
				var marca := {
					"dias": int(entrada["dias"]),
					"puntos": int(entrada["puntos"]),
					"fecha": str(entrada.get("fecha", "")),
				}
				records.mejores.append(marca)
	for campo in records._campos():
		if json.data.has(campo):
			records.set(campo, int(json.data[campo]))
	return records


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


func resumen() -> String:
	if partidas_jugadas == 0:
		return "Todavia no hay recuerdos del tambor: esta sera tu primera partida."

	var porcentaje := 0.0
	if faroles_usados > 0:
		porcentaje = 100.0 * faroles_acertados / faroles_usados
	return (
		(
			"Record: %d dia(s) sobrevividos y %d puntos en una sola partida, en %d partida(s) jugada(s). "
			% [dias_maximos, puntos_maximos, partidas_jugadas]
		)
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
