# assets

Esta carpeta aloja los **recursos visuales y de audio** del juego gráfico (Godot):

- **Imágenes**: iconos, texturas, sprites.
- **Sonidos**: efectos de gatillo, disparo, click vacío.
- **Fuentes**: tipografías personalizadas.

## audio/

- `disparo.wav` — se reproduce en cada disparo resuelto (acierto o fallo).
- `derrota.wav` — se reproduce junto a `disparo.wav` cuando el disparo es una bala.
- `victoria.wav` — se reproduce al sobrevivir la ronda 8.

Los tres son **sintetizados por código** (`audio/synth_sfx.py`, solo
librería estándar de Python — `python3 synth_sfx.py` los regenera en el
mismo sitio), no grabaciones ni assets de terceros: sirven de placeholder
limpio, sin licencia que gestionar, y se pueden sustituir por SFX grabados
más adelante sin tocar nada del lado de Godot (mismos nombres de archivo,
mismos `AudioStreamPlayer` en `MainGame.tscn`).
