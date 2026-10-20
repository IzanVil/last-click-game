class_name Paleta
extends RefCounted

const NEGRO := Color(0.039, 0.039, 0.039, 1)
const GRIS_PLOMO := Color(0.165, 0.165, 0.165, 1)
const BRONCE := Color(0.545, 0.451, 0.333, 1)
const OXIDO := Color(0.545, 0.227, 0.227, 1)
const ROJO := Color(0.8, 0.0, 0.0, 1)

const BRONCE_CLARO := Color(0.847, 0.780, 0.675, 1)
const BRONCE_APAGADO := Color(0.663, 0.596, 0.494, 1)
const GRIS_CLARO := Color(0.290, 0.290, 0.290, 1)
const BRONCE_VIVO := Color(0.788, 0.647, 0.365, 1)


static func aclarar(color: Color, cantidad: float) -> Color:
	return color.lerp(Color.WHITE, cantidad)
