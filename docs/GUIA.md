# 🎯 Guía del proyecto

Este documento describe la mecánica y las reglas de los dos juegos del repositorio,
además de cómo ampliarlos y modificarlos.

## ⚙️ Mecánica de la ruleta rusa

La idea es muy sencilla y se repite en ambas versiones:

1. El revólver tiene **6 huecos** en el tambor.
2. Se introduce **una sola bala** en una posición aleatoria (de 1 a 6).
3. El jugador elige un número del 1 al 6 y «dispara».
4. Si su número coincide con la posición de la bala → **BOOM** (pierde).
   Si no coincide → **Click** (sobrevive).

## 🐍 versión de terminal (Python)

- Archivo: `terminal/ruleta.py`
- Dependencias: **ninguna** (solo la librería estándar de Python 3.6+).
- Ejecución: `python3 ruleta.py`
- Interactúa por entrada/salida estándar.

### Cómo modificar la lógica

El corazón del juego está en la función `jugar()`:

```python
posicion_bala = random.randint(1, 6)
```

Si quieres cambiar el número de huecos del tambor, basta con modificar el `6`
por el valor deseado (por ejemplo, `8` para un tambor más grande).

## 🎮 versión gráfica (Godot)

- Carpeta: `2d/`
- Motor: **Godot 4.6+**
- Escena principal: `2d/scenes/MainGame.tscn`
- Lógica: `2d/MainGame.gd`

### Cómo modificar la lógica

El script `MainGame.gd` usa una etiqueta (`Resultado`), un campo de texto
(`EntradaNumero`) y un botón (`DispararBtn`). La comprobación es:

```gdscript
if numero == posicion_bala:
    # pierde
else:
    # sobrevive
```

Para cambiar el rango de números basta editar el `6` en `randi_range(1, 6)`
y el límite de validación (`if numero < 1 or numero > 6`).

## 🧑‍🔧 Ampliaciones sugeridas

Consulta la **Hoja de ruta** del `README.md` para ver ideas de mejora como:

- Modo «borracho».
- Múltiples balas.
- Selector de dificultad.

## 🗂️ Estructura de carpetas

```
russian-roulette-2d/
├── README.md
├── LICENSE
├── docs/
│   └── GUIA.md
├── terminal/
│   └── ruleta.py
└── 2d/
    ├── project.godot
    ├── MainGame.gd
    ├── scenes/
    │   └── MainGame.tscn
    └── assets/
```
