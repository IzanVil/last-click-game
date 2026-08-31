class_name Paleta
extends RefCounted
## Paleta del juego, en un solo sitio.
##
## Cinco colores y nada mas fuera de ellos: negro de taller cerrado, gris
## plomo de la chapa, bronce envejecido de los herrajes, oxido de lo que
## lleva ahi demasiado tiempo y un rojo punzante reservado para el peligro.
## Los "derivados" no amplian la paleta: son el mismo bronce aclarado u
## oscurecido para que un texto largo se pueda leer sobre negro.
##
## Vive aparte porque lo consumen la vista entera (TamborView, FondoTaller,
## Vineta, los iconos del HUD y MainGame) y conviene que cambiarla sea
## tocar un archivo. El tema de la interfaz (assets/tema/juicio.tres) lleva
## los mismos valores escritos a mano: un .tres no puede leer constantes de
## un script, asi que si aqui cambia algo, hay que cambiarlo alli tambien.

## #0a0a0a — el fondo de todo.
const NEGRO := Color(0.039, 0.039, 0.039, 1)
## #2a2a2a — chapa en sombra, huecos sin explorar.
const GRIS_PLOMO := Color(0.165, 0.165, 0.165, 1)
## #8b7355 — bronce envejecido: herrajes, aros, remaches, titulos.
const BRONCE := Color(0.545, 0.451, 0.333, 1)
## #8b3a3a — oxido: lo que ya se probo y salio mal, el rival.
const OXIDO := Color(0.545, 0.227, 0.227, 1)
## #cc0000 — rojo punzante. Solo peligro: la bala, la muerte, el calor.
const ROJO := Color(0.8, 0.0, 0.0, 1)

# --- Derivados (el mismo bronce, mas claro o mas apagado) --------------------

## Texto principal: bronce aclarado hasta ser comodo de leer sobre negro.
const BRONCE_CLARO := Color(0.847, 0.780, 0.675, 1)
## Texto secundario y pistas: bronce apagado.
const BRONCE_APAGADO := Color(0.663, 0.596, 0.494, 1)
## Metal ya probado, sin brillo.
const GRIS_CLARO := Color(0.290, 0.290, 0.290, 1)
## Bronce encendido: lo que esta vivo ahora mismo (foco, tension, aciertos).
const BRONCE_VIVO := Color(0.788, 0.647, 0.365, 1)


## Aclara un color hacia el blanco. Lo usa el ajuste de alto contraste, que
## sube el tono de toda la interfaz sin cambiar el color de cada cosa (el
## bronce sigue siendo bronce, solo que mas claro).
static func aclarar(color: Color, cantidad: float) -> Color:
	return color.lerp(Color.WHITE, cantidad)
