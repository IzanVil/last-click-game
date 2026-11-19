class_name Apariencia
extends RefCounted

const TAMANO_TEXTO := 16
const AUMENTO_TEXTO := 4

const LADO_ICONO := 18.0

const MEZCLA_CONTRASTE := 0.55

const TIPOS_CON_COLOR_EN_EL_TEMA := ["Button", "CheckBox", "OptionButton", "LineEdit"]
const COLORES_EN_EL_TEMA := ["font_color", "font_hover_color", "font_pressed_color"]

var ajustes := Ajustes.new()

var _raiz: Control
var _colores_originales: Dictionary = {}
var _tamanos_originales: Dictionary = {}
var _colores_tema_originales: Dictionary = {}


func _init(raiz: Control) -> void:
	_raiz = raiz
	_recordar_estilos(raiz)


func aplicar(iconos: Array[Icono]) -> void:
	_aplicar_tamano_de_texto(iconos)
	_aplicar_contraste(iconos)


func con_contraste(color: Color) -> Color:
	return Paleta.aclarar(color, MEZCLA_CONTRASTE) if ajustes.alto_contraste else color


func _recordar_estilos(nodo: Node) -> void:
	if nodo is Label or nodo is Button or nodo is RichTextLabel:
		var control := nodo as Control
		if control.has_theme_color_override("font_color"):
			_colores_originales[control] = control.get_theme_color("font_color")
		if control.has_theme_font_size_override("font_size"):
			_tamanos_originales[control] = control.get_theme_font_size("font_size")
		if control.has_theme_font_size_override("normal_font_size"):
			_tamanos_originales[control] = control.get_theme_font_size("normal_font_size")
	for hijo in nodo.get_children():
		_recordar_estilos(hijo)


func _aplicar_tamano_de_texto(iconos: Array[Icono]) -> void:
	var aumento := AUMENTO_TEXTO if ajustes.texto_grande else 0
	if _raiz.theme != null:
		_raiz.theme.default_font_size = TAMANO_TEXTO + aumento
	for control in _tamanos_originales:
		var original: int = _tamanos_originales[control]
		if control is RichTextLabel:
			control.add_theme_font_size_override("normal_font_size", original + aumento)
		else:
			control.add_theme_font_size_override("font_size", original + aumento)
	for icono in iconos:
		icono.lado = LADO_ICONO + aumento


func _aplicar_contraste(iconos: Array[Icono]) -> void:
	for control in _colores_originales:
		var original: Color = _colores_originales[control]
		control.add_theme_color_override("font_color", con_contraste(original))
	for icono in iconos:
		icono.color = con_contraste(Paleta.BRONCE)

	if _raiz.theme == null:
		return
	for tipo in TIPOS_CON_COLOR_EN_EL_TEMA:
		for nombre in COLORES_EN_EL_TEMA:
			if not _raiz.theme.has_color(nombre, tipo):
				continue
			var clave := "%s/%s" % [tipo, nombre]
			if not _colores_tema_originales.has(clave):
				_colores_tema_originales[clave] = _raiz.theme.get_color(nombre, tipo)
			var original: Color = _colores_tema_originales[clave]
			_raiz.theme.set_color(nombre, tipo, con_contraste(original))
