# Guía del proyecto

Este documento describe la mecánica y las reglas de los dos juegos del
repositorio, además de cómo ampliarlos y modificarlos.

## Mecánica de la ruleta rusa

Las dos versiones ya no comparten mecánica: la terminal estrena un rediseño
("El Tambor del Juicio", ver la Fase 1 de la hoja de ruta del `README.md`);
la versión gráfica conserva por ahora el clásico de 8 rondas hasta que se
porte el mismo rediseño.

### Terminal — El Tambor del Juicio

1. El tambor tiene **8 huecos** y una única bala colocada al azar.
2. Cada turno el jugador elige: **disparar** o **retirarse**.
   - Retirarse cobra los puntos que hay en juego (la partida empieza con
     100) y termina la partida.
   - Disparar y fallar (cartucho vacío) dobla los puntos en juego, mueve la
     bala a otro hueco según un patrón oculto y revela una pista veraz sobre
     su nueva posición.
   - Disparar y acertar la bala es un **BOOM**: se pierden todos los puntos
     en juego.
3. El patrón de movimiento (avanza, retrocede, salta de dos en dos o
   espejo) se sortea al empezar la partida y no se le dice al jugador: se
   deduce comparando las pistas de varios disparos.

### Gráfica (Godot) — el clásico de 8 rondas

1. El tambor tiene **10 huecos**, numerados del 1 al 10.
2. El juego consta de **8 rondas**. En cada ronda se cargan más balas que en la
   anterior: de 1 bala en la ronda 1 hasta 8 balas en la ronda 8.
3. El jugador elige una posición del tambor y «dispara».
4. Si el hueco elegido es una **bala** → **BOOM** (pierde y la partida se reinicia).
   Si está **vacío** → **Click** (sobrevive y avanza a la siguiente ronda).
5. Sobrevivir a las 8 rondas supone la **victoria**.

#### Tabla de dificultad por ronda

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

- Archivos: `terminal/ruleta.py` (interfaz, sin lógica propia) +
  `terminal/estado.py`, `terminal/pistas.py`, `terminal/apuestas.py` (lógica
  pura, sin `input()`/`print()`, igual de fácil de testear que
  `RuletaEstado.gd` en la versión Godot).
- Dependencias: **ninguna** (solo la librería estándar de Python 3.11+).
- Ejecución: `./run.sh`, o directamente `python3 terminal/ruleta.py`.
- Interactúa por entrada/salida estándar con interfaz en colores y tambor ASCII.

### Cómo modificar la lógica

- `estado.HUECOS` (por defecto 8) y `estado.PATRONES` controlan el tamaño
  del tambor y los patrones de movimiento de la bala disponibles. Añadir un
  patrón nuevo implica sumarlo a `PATRONES` y a la función `_mover()` en
  `estado.py`.
- `pistas.TIPOS_PISTA` en `pistas.py` define los tipos de pista disponibles
  (`paridad`, `mitad`, `relativa`); cada uno es una rama de
  `generar_pista()`.
- `ruleta.APUESTA_BASE` (por defecto 100) es la apuesta inicial de cada
  partida; la lógica de doblar/perder/retirarse vive en `apuestas.Apuesta`.

`ruleta.py` importa estos tres módulos con un `try/except` (relativo si se
usa como paquete instalado, absoluto si se ejecuta como script suelto): si
añades un cuarto módulo de lógica, sigue el mismo patrón de import.

### Tests

Hay una batería de pruebas por módulo (`test_estado.py`, `test_pistas.py`,
`test_apuestas.py`, `test_ruleta.py`):

```bash
cd terminal && python3 -m unittest discover -s . -v
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

Consulta la **Hoja de ruta** del `README.md` para el detalle completo del
rediseño «El Tambor del Juicio» (farol, eventos, días de vida, port a
Godot, multijugador, récords...) y otras ideas sueltas como el modo
«borracho» o los efectos de sonido de gatillo.

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
│   ├── estado.py
│   ├── pistas.py
│   ├── apuestas.py
│   ├── test_ruleta.py
│   ├── test_estado.py
│   ├── test_pistas.py
│   └── test_apuestas.py
└── 2d/
    ├── project.godot
    ├── MainGame.gd
    ├── RuletaEstado.gd
    ├── scenes/
    │   └── MainGame.tscn
    └── assets/
```
