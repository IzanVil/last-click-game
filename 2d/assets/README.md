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
| `disparo.wav` | Cuando el disparo encuentra la bala: chasquido seco. |
| `derrota.wav` | Junto a `disparo.wav` en ese mismo momento: el golpe sordo del final. |
| `clic.wav` | Cartucho vacío: el clic hueco del percutor cayendo sobre nada. |
| `victoria.wav` | Al retirarse a tiempo con los puntos. |
| `engranaje.wav` | Al girar el tambor: empezar partida, cada disparo y el evento «clic metálico». |
| `fallo.wav` | Golpe seco: el trinquete al parar el tambor, y el farol fallido. |
| `marca.wav` | Farol acertado (campanilla corta y aguda). |
| `calor.wav` | Evento «tambor caliente»: un zumbido que sube de tono. |
| `musica_base.wav` | Banda sonora, capa de siempre: bordón grave y arpegio de piano en La menor a 70 pulsos por minuto. |
| `musica_tension.wav` | Capa que se superpone a la anterior cuando quedan tres huecos o menos: latido y tritono. |

Todos son **sintetizados por código** (`audio/synth_sfx.py`, solo librería
estándar de Python — `python3 synth_sfx.py` los regenera en el mismo
sitio), no grabaciones ni assets de terceros: sirven de placeholder limpio,
sin licencia que gestionar, y se pueden sustituir por SFX grabados más
adelante sin tocar nada del lado de Godot (mismos nombres de archivo,
mismos `AudioStreamPlayer` en `MainGame.tscn`).

Las **dos capas de música** duran exactamente lo mismo (8 compases a 70
BPM = 604 800 muestras) y se lanzan a la vez, así que van en fase mientras
compartan `pitch_scale`: por eso la tensión puede entrar y salir sin cortar
la música. Están hechas para encadenar en bucle —las frecuencias sostenidas
caben un número entero de veces en el bucle y las colas de las notas dan la
vuelta al principio— y van a 22050 Hz, la mitad que los efectos, porque son
graves y así ocupan la mitad. El bucle se activa desde
`MainGame._arrancar_musica()` y no desde el `.import`: Godot 4.7 escribe ahí
`edit/loop_mode` pero no lo traslada al recurso cargado.

## fonts/

Courier Prime (interfaz) y Special Elite (título). A diferencia del audio,
estas **sí son de terceros**: su procedencia, sus licencias (OFL 1.1 y
Apache 2.0) y las obligaciones que implican al redistribuir están en
[`fonts/README.md`](fonts/README.md).

## tema/

`juicio.tres`, el `Theme` que viste toda la interfaz: las dos tipografías y
el aspecto de chapa y latón de botones, campos, desplegables, deslizadores
y paneles (con los mismos colores que `Paleta.gd`, escritos a mano: un
`.tres` no puede leer constantes de un script). Se
asigna al nodo raíz de `scenes/MainGame.tscn` y de ahí lo hereda todo lo
demás.
