# assets

Esta carpeta aloja los **recursos visuales y de audio** del juego gráfico (Godot).

Casi nada de lo que hay aquí es una imagen: el tambor, los engranajes del
fondo, la viñeta y los resplandores se **dibujan por código** (`_draw()` en
`TamborView.gd`, `FondoTaller.gd` y `Vineta.gd`), y el aspecto de chapa de
los botones sale de `StyleBoxFlat` en el tema. Así el tambor encaja con
cualquier dificultad (6, 8 o 10 huecos) sin tener tres sprites, y no hay
assets de terceros que licenciar salvo las dos tipografías.

## audio/

| Archivo | Cuándo suena |
|---------|--------------|
| `disparo.wav` | En cada disparo resuelto (acierte o falle). |
| `derrota.wav` | Junto a `disparo.wav` cuando el disparo encuentra la bala. |
| `victoria.wav` | Al retirarse a tiempo con los puntos. |
| `engranaje.wav` | Al girar el tambor: empezar partida, tensión antes de un disparo o farol, y evento «clic metálico». |
| `marca.wav` | Farol acertado (campanilla corta y aguda). |
| `fallo.wav` | Farol fallido (golpe seco: ni mata ni premia). |
| `ambiente.wav` | Bordón grave en bucle mientras el juego está abierto; sube de volumen durante la partida y se acelera con el tambor caliente. |

Todos son **sintetizados por código** (`audio/synth_sfx.py`, solo librería
estándar de Python — `python3 synth_sfx.py` los regenera en el mismo
sitio), no grabaciones ni assets de terceros: sirven de placeholder limpio,
sin licencia que gestionar, y se pueden sustituir por SFX grabados más
adelante sin tocar nada del lado de Godot (mismos nombres de archivo,
mismos `AudioStreamPlayer` en `MainGame.tscn`).

`ambiente.wav` es el único pensado para **encadenar en bucle**: dura 6 s
exactos y todas sus frecuencias caben un número entero de veces en ellos,
así que el final empalma con el principio sin chasquido. Va a 22050 Hz (la
mitad que el resto) porque son todo graves y así ocupa la mitad. El bucle
se activa desde `MainGame._arrancar_ambiente()` y no desde el `.import`:
Godot 4.7 escribe ahí `edit/loop_mode` pero no lo traslada al recurso
cargado.

## fonts/

Courier Prime (interfaz) y Special Elite (título). A diferencia del audio,
estas **sí son de terceros**: su procedencia, sus licencias (OFL 1.1 y
Apache 2.0) y las obligaciones que implican al redistribuir están en
[`fonts/README.md`](fonts/README.md).

## tema/

`juicio.tres`, el `Theme` que viste toda la interfaz: las dos tipografías y
el aspecto de chapa y latón de botones, campos, desplegables y paneles. Se
asigna al nodo raíz de `scenes/MainGame.tscn` y de ahí lo hereda todo lo
demás.
