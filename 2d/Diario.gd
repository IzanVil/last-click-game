class_name Diario
extends RefCounted

const RUTA_POR_DEFECTO := "user://diario.json"

const DIFICULTAD := "normal"

var resultados: Dictionary = {}


static func clave_de_hoy() -> String:
	return clave_de(Time.get_date_dict_from_system())


static func clave_de(fecha: Dictionary) -> String:
	return "%04d-%02d-%02d" % [int(fecha["year"]), int(fecha["month"]), int(fecha["day"])]


static func semilla_de_hoy() -> int:
	return semilla_de(Time.get_date_dict_from_system())


static func semilla_de(fecha: Dictionary) -> int:
	return int(fecha["year"]) * 10000 + int(fecha["month"]) * 100 + int(fecha["day"])


func jugado_hoy() -> bool:
	return resultados.has(clave_de_hoy())


func resultado_de_hoy() -> Dictionary:
	return resultados.get(clave_de_hoy(), {})


func registrar(dias: int, puntos: int, clave := "") -> void:
	var dia := clave if clave != "" else clave_de_hoy()
	var anterior: Dictionary = resultados.get(dia, {})
	if not anterior.is_empty():
		var mejor_dias := int(anterior["dias"])
		if dias < mejor_dias:
			return
		if dias == mejor_dias and puntos <= int(anterior["puntos"]):
			return
	resultados[dia] = {"dias": dias, "puntos": puntos}


func racha(hoy := Time.get_date_dict_from_system()) -> int:
	var dia := int(Time.get_unix_time_from_datetime_dict(_a_medianoche(hoy)))
	if not resultados.has(clave_de(hoy)):
		dia -= 86400
	var seguidos := 0
	while resultados.has(clave_de(Time.get_date_dict_from_unix_time(dia))):
		seguidos += 1
		dia -= 86400
	return seguidos


static func _a_medianoche(fecha: Dictionary) -> Dictionary:
	return {
		"year": int(fecha["year"]),
		"month": int(fecha["month"]),
		"day": int(fecha["day"]),
		"hour": 0,
		"minute": 0,
		"second": 0,
	}


func resumen() -> String:
	var seguidos := racha()
	var cola := ""
	if seguidos > 1:
		cola = "  ·  %d dias seguidos" % seguidos

	var hoy := resultado_de_hoy()
	if hoy.is_empty():
		return "Reto de hoy (%s): sin jugar%s" % [clave_de_hoy(), cola]
	return (
		"Reto de hoy (%s): %d dia(s) y %d puntos%s"
		% [clave_de_hoy(), int(hoy["dias"]), int(hoy["puntos"]), cola]
	)


static func cargar(ruta := RUTA_POR_DEFECTO) -> Diario:
	var archivo := FileAccess.open(ruta, FileAccess.READ)
	if archivo == null:
		return Diario.new()
	var texto := archivo.get_as_text()
	archivo.close()

	var json := JSON.new()
	if json.parse(texto) != OK or not (json.data is Dictionary):
		return Diario.new()

	var diario := Diario.new()
	var leidos: Variant = json.data.get("resultados", {})
	if leidos is Dictionary:
		for dia: String in leidos:
			var entrada: Variant = leidos[dia]
			if entrada is Dictionary and entrada.has("dias") and entrada.has("puntos"):
				diario.resultados[dia] = {
					"dias": int(entrada["dias"]),
					"puntos": int(entrada["puntos"]),
				}
	return diario


func guardar(ruta := RUTA_POR_DEFECTO) -> bool:
	var carpeta := ruta.get_base_dir()
	if not DirAccess.dir_exists_absolute(carpeta):
		DirAccess.make_dir_recursive_absolute(carpeta)

	var archivo := FileAccess.open(ruta, FileAccess.WRITE)
	if archivo == null:
		return false
	archivo.store_string(JSON.stringify({"resultados": resultados}, "  "))
	archivo.close()
	return true
