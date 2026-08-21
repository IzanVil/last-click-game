# Guía del proyecto

Este documento describe la mecánica y las reglas de los dos juegos del
repositorio, además de cómo ampliarlos y modificarlos.

## Mecánica de la ruleta rusa

La idea se repite en ambas versiones, subiendo la tensión ronda a ronda:

1. El tambor tiene **10 huecos**, numerados del 1 al 10.
2. El juego consta de **8 rondas**. En cada ronda se cargan más balas que en la
   anterior: de 1 bala en la ronda 1 hasta 8 balas en la ronda 8.
3. El jugador elige una posición del tambor y «dispara».
4. Si el hueco elegido es una **bala** → **BOOM** (pierde y la partida se reinicia).
   Si está **vacío** → **Click** (sobrevive y avanza a la siguiente ronda).
5. Sobrevivir a las 8 rondas supone la **victoria**.

### Tabla de dificultad por ronda

| Ronda | Huecos | Balas | Vacíos |
|:-----:|:------:|:-----:|:------:|
| 1 | 10 | 1 | 9 |
| 2 | 10 | 2 | 8 |
| 3 | 10 | 3 | 7 |
| 4 | 10 | 4 | 6 |
| 5 | 10 | 5 | 5 |
| 6 | 10 | 6 | 4 |
| 7 | 10 | 7 | 3 |
| 8 | 10 | 8 | 2 |

## Versión de terminal (Python)

- Archivo: `terminal/ruleta.py`
- Dependencias: **ninguna** (solo la librería estándar de Python 3.11+).
- Ejecución: `./run.sh`, o directamente `python3 terminal/ruleta.py`.
- Interactúa por entrada/salida estándar con interfaz en colores y tambor ASCII.

### Cómo modificar la lógica

Los valores clave están al comienzo del archivo:

```python
HUECOS = 10
RONDAS = 8
```

- `HUECOS` controla el tamaño del tambor.
- La dificultad por ronda se deriva del número de ronda (ronda N → N balas).
  Si quieres una curva distinta, basta con cambiar el cálculo en `jugar()`
  (por ejemplo, `balas = min(balas + 2, HUECOS)` para que suba más rápido).

### Tests

La batería de pruebas se encuentra en `terminal/test_ruleta.py`:

```bash
cd terminal && python3 -m unittest test_ruleta -v
```

## Versión gráfica (Godot)

- Carpeta: `2d/`
- Motor: **Godot 4.7+**
- Escena principal: `2d/scenes/MainGame.tscn`
- Lógica del juego (sin UI): `2d/RuletaEstado.gd`
- Vista (Label/ColorRect/Tween): `2d/MainGame.gd`

`RuletaEstado.gd` no conoce nodos ni UI: solo lleva la ronda actual y las
balas del tambor, y emite señales (`ronda_preparada`, `entrada_invalida`,
`impacto`, `click_seguro`, `partida_ganada`). `MainGame.gd` se limita a
escuchar esas señales y traducirlas a texto en pantalla y animaciones.

### Cómo modificar la lógica

La configuración clave está al principio de `RuletaEstado.gd`:

```gdscript
const HUECOS := 10
const RONDAS := 8
const BALAS_POR_RONDA := [1, 2, 3, 4, 5, 6, 7, 8]
```

- `HUECOS` cambia el tamaño del tambor.
- `RONDAS` cambia el número de rondas.
- `BALAS_POR_RONDA` define cuántas balas hay en cada ronda; puedes editarlo
  para diseñar tu propia curva de dificultad.

El feedback visual (flash rojo/verde/dorado) se gestiona en `MainGame.gd`,
en `_flash(color)`.

## Lanzadores

| Archivo | Plataforma | Acción |
|---------|-----------|--------|
| `run.sh` | Linux / macOS | Juego en terminal (`-g` abre Godot) |
| `run.bat` | Windows | Juego en terminal (`-g` abre Godot) |

## Ampliaciones sugeridas

Consulta la **Hoja de ruta** del `README.md` para más ideas:

- Modo «borracho».
- Selector de dificultad (tambores de otros tamaños).
- Sistema de puntos, rachas y récords.
- Efectos de sonido de gatillo.
- Animación del tambor girando en Godot.

## Estructura de carpetas

```
russian-roulette-2d/
├── README.md
├── LICENSE
├── pyproject.toml
├── instalar.sh
├── instalar.bat
├── run.sh
├── run.bat
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   └── GUIA.md
├── terminal/
│   ├── __init__.py
│   ├── ruleta.py
│   └── test_ruleta.py
└── 2d/
    ├── project.godot
    ├── MainGame.gd
    ├── RuletaEstado.gd
    ├── scenes/
    │   └── MainGame.tscn
    └── assets/
```
