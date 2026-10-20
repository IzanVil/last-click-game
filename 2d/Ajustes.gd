class_name Ajustes
extends RefCounted

const RUTA_POR_DEFECTO := "user://ajustes.json"

var efectos_reducidos := false

var texto_grande := false

var alto_contraste := false

var sonido := true

var volumen_musica := 0.7
var volumen_efectos := 0.9

var pantalla_completa := false


static func cargar(ruta := RUTA_POR_DEFECTO) -> Ajustes:
	var archivo := FileAccess.open(ruta, FileAccess.READ)
	if archivo == null:
		return Ajustes.new()
	var texto := archivo.get_as_text()
	archivo.close()

	var json := JSON.new()
	if json.parse(texto) != OK or not (json.data is Dictionary):
		return Ajustes.new()

	var ajustes := Ajustes.new()
	for campo in ajustes._campos():
		if not json.data.has(campo):
			continue
		if typeof(ajustes.get(campo)) == TYPE_BOOL:
			ajustes.set(campo, bool(json.data[campo]))
		else:
			ajustes.set(campo, clampf(float(json.data[campo]), 0.0, 1.0))
	return ajustes


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
