# Guía del proyecto

Este documento describe la mecánica y las reglas de los dos juegos del
repositorio, además de cómo ampliarlos y modificarlos.

## Mecánica de la ruleta rusa

Las dos versiones ya no comparten mecánica: la terminal estrena un rediseño
("El Tambor del Juicio", ver la hoja de ruta del `README.md`, Fases 1 y 2
ya en la terminal); la versión gráfica conserva por ahora el clásico de 8
rondas hasta que se porte el mismo rediseño.

### Terminal — El Tambor del Juicio

1. El tambor tiene **8 huecos** y una única bala colocada al azar. La
   partida no termina en la primera muerte: el objetivo es acumular **días
   de vida** (cada día son 3 disparos sobrevividos, `DISPAROS_POR_DIA`).
2. Cada turno el jugador elige entre **disparar**, **retirarse** o, si le
   quedan, **marcar**:
   - Retirarse cobra los puntos que hay en juego (la partida empieza con
     100) y termina la partida.
   - Disparar y fallar (cartucho vacío) dobla los puntos en juego, mueve la
     bala a otro hueco según un patrón oculto y revela una pista sobre su
     nueva posición.
   - Disparar y acertar la bala es un **BOOM**: se pierden todos los puntos
     en juego y termina la partida.
   - Marcar declara un hueco "seguro" sin disparar, gastando una de las **3
     marcas** de la partida (se gasta acierte o falle). Acertar da un bono
     de puntos sin doblar; fallar solo cuesta la marca, sin mover la bala
     ni terminar la partida.
3. El patrón de movimiento (avanza, retrocede, salta de dos en dos o
   espejo) se sortea al empezar la partida y no se le dice al jugador: se
   deduce comparando las pistas de varios disparos.
4. Tras un disparo fallido puede ocurrir un **evento aleatorio**:
   `clic_metalico` desplaza la bala un paso extra (fuera del patrón normal)
   y `tambor_caliente` hace que la siguiente pista sea mentirosa (afirma lo
   contrario de la posición real, con el mismo aspecto que una veraz).
5. El tambor ASCII colorea cada hueco según lo que se sabe de él: **verde**
   si un farol confirmó que estaba vacío, **rojo** si un farol reveló la
   bala ahí, **amarillo** si es un candidato que cumple con el cruce de
   *todas* las pistas vigentes, **gris** si ya se disparó ahí alguna vez.
   Si el cruce de pistas se queda sin candidatos, es señal de que alguna
   pista reciente mentía.
6. Al terminar la partida se resume en una frase lo ocurrido (días
   sobrevividos, faroles lanzados/acertados, eventos sufridos).

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
  `terminal/estado.py`, `terminal/pistas.py`, `terminal/apuestas.py`,
  `terminal/farol.py`, `terminal/eventos.py`, `terminal/historial.py`
  (lógica pura, sin `input()`/`print()`, igual de fácil de testear que
  `RuletaEstado.gd` en la versión Godot).
- Dependencias: **ninguna** (solo la librería estándar de Python 3.11+).
- Ejecución: `./run.sh`, o directamente `python3 terminal/ruleta.py`.
- Interactúa por entrada/salida estándar con interfaz en colores y tambor ASCII.

### Cómo modificar la lógica

- `estado.HUECOS` (por defecto 8), `estado.PATRONES` y
  `estado.DISPAROS_POR_DIA` (por defecto 3) controlan el tamaño del tambor,
  los patrones de movimiento disponibles y la duración de un "día". Añadir
  un patrón nuevo implica sumarlo a `PATRONES` y a la función `_mover()` en
  `estado.py`.
- `pistas.TIPOS_PISTA` en `pistas.py` define los tipos de pista disponibles
  (`paridad`, `mitad`, `relativa`); cada uno es una rama de
  `generar_pista()`, que acepta `mentir=True` para invertir la respuesta
  (lo usa el evento `tambor_caliente`) y devuelve una `Pista(texto,
  candidatos)`: `candidatos` son los huecos consistentes con esa
  afirmación. `pistas.interseccion()` los cruza para pintar el tambor.
- `ruleta.APUESTA_BASE` (por defecto 100) es la apuesta inicial de cada
  partida y `ruleta.BONO_MARCA_ACERTADA` (por defecto 50) el bono de un
  farol acertado; la lógica de doblar/perder/retirarse/sumar bono vive en
  `apuestas.Apuesta`.
- `farol.MARCAS_INICIALES` (por defecto 3) son las marcas por partida;
  `farol.Farol` resuelve si un hueco marcado estaba vacío.
- `eventos.PROBABILIDAD` (por defecto 0.25) y `eventos.TIPOS_EVENTO`
  controlan cuánto y qué tan a menudo interfieren los eventos aleatorios
  tras un disparo fallido.
- `historial.Historial` acumula faroles y eventos de la partida;
  `historial.resumen()` genera la frase final. `ruleta.calcular_estados()`
  combina marcadas/resultados de farol/candidatos en el diccionario que
  colorea el tambor (`ruleta.COLORES_ESTADO`, `ruleta.GLIFOS_ESTADO`).

`ruleta.py` importa estos seis módulos con un `try/except` (relativo si se
usa como paquete instalado, absoluto si se ejecuta como script suelto): si
añades un módulo de lógica más, sigue el mismo patrón de import.

### Tests

Hay una batería de pruebas por módulo (`test_estado.py`, `test_pistas.py`,
`test_apuestas.py`, `test_farol.py`, `test_eventos.py`, `test_historial.py`,
`test_ruleta.py`):

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
│   ├── farol.py
│   ├── eventos.py
│   ├── historial.py
│   ├── test_ruleta.py
│   ├── test_estado.py
│   ├── test_pistas.py
│   ├── test_apuestas.py
│   ├── test_farol.py
│   ├── test_eventos.py
│   └── test_historial.py
└── 2d/
    ├── project.godot
    ├── MainGame.gd
    ├── RuletaEstado.gd
    ├── scenes/
    │   └── MainGame.tscn
    └── assets/
```
