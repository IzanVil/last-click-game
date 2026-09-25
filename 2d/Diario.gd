class_name Diario
extends RefCounted
## El reto del dia: un tambor igual para todos, que cambia a medianoche.
##
## La semilla ES la fecha (AAAAMMDD leido como numero), no un hash de
## ella. Asi el numero cabe de sobra en el rango de Azar.MAXIMO, se puede
## teclear a mano en el campo de semilla del menu para repetir el reto de
## cualquier dia pasado, y quien lea el codigo entiende de un vistazo de
## donde sale.
##
## La fecha es la LOCAL del jugador, no UTC: sin tabla de clasificacion
## online, "el reto de hoy" significa el de tu hoy. Cambiar a UTC seria
## lo suyo el dia que dos personas quieran comparar resultados de verdad.
##
## De momento solo existe en la version grafica. Llevarlo a la terminal
## pide que una misma semilla de la misma partida en las dos versiones, y
## eso no pasa hoy (Python usa Mersenne Twister y Godot PCG32).

const RUTA_POR_DEFECTO := "user://diario.json"

## El reto siempre se juega en normal. Si respetara la dificultad elegida
## en el menu, "el mismo reto" no seria el mismo: con 6 huecos o con 10
## la partida es otra aunque la bala arranque en el mismo sitio.
const DIFICULTAD := "normal"

## Resultados por dia: "AAAA-MM-DD" -> {"dias": int, "puntos": int}.
## Se guarda el MEJOR intento de cada dia, no el primero: sin tabla
## online el numero es una marca personal, y castigar el primer intento
## solo invita a cerrar el juego a lo bruto para que no cuente.
var resultados: Dictionary = {}


## La fecha local de hoy como "AAAA-MM-DD".
static func clave_de_hoy() -> String:
	return clave_de(Time.get_date_dict_from_system())


## La misma clave para un diccionario de fecha cualquiera, que es lo que
## permite testear los dias de ayer sin tocar el reloj del sistema.
static func clave_de(fecha: Dictionary) -> String:
	return "%04d-%02d-%02d" % [int(fecha["year"]), int(fecha["month"]), int(fecha["day"])]


## La semilla del reto de hoy.
static func semilla_de_hoy() -> int:
	return semilla_de(Time.get_date_dict_from_system())


static func semilla_de(fecha: Dictionary) -> int:
	return int(fecha["year"]) * 10000 + int(fecha["month"]) * 100 + int(fecha["day"])


## Si ya se jugo el reto de hoy.
func jugado_hoy() -> bool:
	return resultados.has(clave_de_hoy())


## El mejor resultado de hoy, o {} si aun no se ha jugado.
func resultado_de_hoy() -> Dictionary:
	return resultados.get(clave_de_hoy(), {})


## Anota un intento, quedandose con el mejor del dia. Mismo criterio que
## el resto del juego: mandan los dias y, a igualdad, los puntos (ver
## Jugador.ganadores).
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


## Dias seguidos jugados contando hacia atras desde hoy.
##
## Si hoy todavia no se ha jugado, la racha se mide desde ayer: estar a
## media mañana sin haber entrado no deberia borrar diez dias seguidos.
## Lo que rompe la racha es saltarse un dia entero.
func racha(hoy := Time.get_date_dict_from_system()) -> int:
	var dia := int(Time.get_unix_time_from_datetime_dict(_a_medianoche(hoy)))
	if not resultados.has(clave_de(hoy)):
		dia -= 86400
	var seguidos := 0
	while resultados.has(clave_de(Time.get_date_dict_from_unix_time(dia))):
		seguidos += 1
		dia -= 86400
	return seguidos


## Una fecha a las 00:00, que es lo que espera
## Time.get_unix_time_from_datetime_dict para poder restar dias enteros.
static func _a_medianoche(fecha: Dictionary) -> Dictionary:
	return {
		"year": int(fecha["year"]),
		"month": int(fecha["month"]),
		"day": int(fecha["day"]),
		"hour": 0,
		"minute": 0,
		"second": 0,
	}


## Frase para el menu: en que estado esta el reto de hoy.
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


## Carga el diario desde disco. Un archivo que no existe o esta corrupto
## devuelve un diario vacio en vez de reventar, igual que Records.cargar.
static func cargar(ruta := RUTA_POR_DEFECTO) -> Diario:
	var archivo := FileAccess.open(ruta, FileAccess.READ)
	if archivo == null:
		return Diario.new()
	var texto := archivo.get_as_text()
	archivo.close()

	# JSON.new().parse() y no JSON.parse_string(), por lo mismo que en
	# Records.cargar: un archivo corrupto es un caso previsto y no
	# merece un "Parse JSON failed" en el log.
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


## Guarda el diario en disco. Devuelve true si se pudo escribir.
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
