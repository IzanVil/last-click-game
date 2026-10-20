class_name Maquina
extends RefCounted

const META_TWEEN := "tween_maquina"

const CARACTERES_POR_SEGUNDO := 55.0


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
