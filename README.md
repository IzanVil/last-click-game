<p align="center">
  <img src="2d/icon.svg" alt="Russian Roulette" width="120">
</p>

<h1 align="center">🔫 Russian Roulette</h1>

<p align="center">
  <strong>¿Te sientes con suerte? El tambor gira y la bala te está esperando.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Godot-4.7%2B-478CBF?logo=godotengine&logoColor=white" alt="Godot">
  <img src="https://img.shields.io/badge/estado-en%20desarrollo-yellow" alt="Estado">
  <img src="https://img.shields.io/badge/licencia-MIT-green" alt="Licencia">
  <img src="https://img.shields.io/badge/coverage-97%25-brightgreen" alt="Cobertura">
</p>

---

Una colección de minijuegos de ruleta rusa en **dos sabores**: un clásico de
**terminal** escrito en Python y una versión **gráfica 2D** hecha con Godot.
Desde esta beta, ambas versiones ya no juegan igual: la terminal estrena
**El Tambor del Juicio**, un rediseño centrado en la gestión de riesgo y el
farol; la versión gráfica conserva por ahora la mecánica clásica de 8 rondas
mientras se planea su propio port (ver [Hoja de ruta](#hoja-de-ruta)).

## 🧠 La idea

- **🐍 Terminal — El Tambor del Juicio.** El tambor tiene **8 huecos** y una
  única bala que **se desplaza** tras cada disparo que la falla, siguiendo un
  patrón oculto que debes deducir a partir de las pistas (a veces
  mentirosas) y de eventos aleatorios. En cada turno decides: **te retiras**
  con los puntos que llevas en juego, **disparas** arriesgando que se
  **doblen** (o perderlo todo), o gastas una de tus 3 **marcas** para
  declarar un hueco seguro sin arriesgar el pellejo. El objetivo ya no es
  una única partida: es acumular **días de vida**.
- **🎮 Gráfica (Godot) — el clásico de 8 rondas.** El tambor tiene **10
  huecos** cargados con un número variable de balas. Eliges una posición y
  aprietas el gatillo: si es bala → 💥 *BOOM* (pierdes); si está vacío → 😅
  *Click* (avanzas). Cada ronda se añaden más balas hasta la ronda 8.

> ⚠️ **Descargo de responsabilidad:** es solo un juego de ficción. No existe
> ninguna arma real. Solo diversión para la terminal y la pantalla.

## 📦 Requisitos

| Versión | Tecnología | Requisito |
|---------|-----------|-----------|
| Terminal | 🐍 Python | Python 3.11 o superior |
| Gráfica  | 🎮 Godot | Godot 4.7 o superior |

## ⬇️ Instalación (versión terminal)

La forma más cómoda de jugar es descargar el juego e instalar un **acceso
directo** en tu escritorio: con un doble clic el juego se abre solo.

**1. Descarga e instala [Python 3.11+](https://python.org/downloads/)** si aún
no lo tienes.

**2. Descarga e inicia el instalador:**

- **Linux / macOS** → descarga el proyecto (botón *Code ▾ → Download ZIP*),
  descomprime la carpeta y haz **doble clic** en `instalar.sh` (o en la
  terminal: `./instalar.sh`).
- **Windows** → haz **doble clic** en `instalar.bat`.

El instalador detecta Python, crea el acceso directo en el escritorio y abre
el juego directamente.

> 💡 Si el sistema bloquea el archivo por ser de Internet, abre la terminal y
> ejecútalo tú: `./instalar.sh`. En Windows, si aparece un aviso, pulsa
> *「Más información → Ejecutar de todas formas»*.

## 🚀 Lanzadores rápidos

Incluimos dos lanzadores para que el juego arranque directo sin teclear comandos:

| Archivo | Sistema | Qué hace |
|---------|---------|----------|
| `run.sh` | Linux / macOS | Lanza la ruleta; con `run.sh -g` abre Godot |
| `run.bat` | Windows | Lanza la ruleta; con `run.bat -g` abre Godot |

```bash
# Ejecutar el juego en la terminal (Linux / macOS)
./run.sh

# O abrir el editor Godot
./run.sh -g
```

## 🗂️ Estructura del repositorio

```
russian-roulette-2d/
├── README.md            ← esta documentación
├── LICENSE              ← licencia MIT
├── pyproject.toml       ← metadata, entry point y config de ruff/black/coverage
├── instalar.sh          ← instalador + acceso directo (Linux / macOS)
├── instalar.bat         ← instalador (Windows)
├── run.sh               ← lanzador Linux / macOS
├── run.bat              ← lanzador Windows
├── .github/workflows/   ← CI (tests Python + smoke test Godot)
├── docs/
│   └── GUIA.md          ← guía técnica del proyecto
├── terminal/            ← versión de consola: El Tambor del Juicio
│   ├── ruleta.py        ← interfaz de terminal (pantalla, teclado, colores)
│   ├── estado.py        ← tambor y bala: posición, patrón, días de vida
│   ├── pistas.py        ← generación de pistas (veraces o mentirosas)
│   ├── apuestas.py      ← apuesta doblar-o-retirarse
│   ├── farol.py         ← marcar un hueco como seguro sin disparar
│   ├── eventos.py       ← eventos aleatorios (clic metálico, tambor caliente)
│   └── test_*.py        ← pruebas unitarias de los seis módulos
└── 2d/                  ← versión gráfica
    ├── project.godot    ← proyecto Godot
    ├── RuletaEstado.gd  ← estado y reglas del juego (sin UI)
    ├── MainGame.gd      ← vista: Label/ColorRect/Tween
    ├── scenes/          ← escenas (UI)
    └── assets/          ← recursos visuales
```

## 🐍 Versión de terminal (Python) — El Tambor del Juicio

Ya no es solo elegir un número: gestionas pistas y una apuesta que se dobla
mientras te atrevas a seguir.

### Cómo jugar

Desde la raíz del repositorio:

```bash
./run.sh                       # usa el lanzador (Linux / macOS)
# o directamente:
cd terminal && python3 ruleta.py
```

> 💡 En Windows usa `run.bat`, o `python ruleta.py` en lugar de `python3`.

### Reglas

1. El tambor tiene **8 huecos** y una única bala colocada al azar. La
   partida no acaba en la primera muerte: lo que se mide es cuántos **días
   de vida** aguantas (cada día son 3 disparos sobrevividos).
2. En cada turno eliges entre **(D)isparar**, **(R)etirarte** o, si te
   quedan, **(M)arcar** un hueco como seguro:
   - **Retirarte** cobra los puntos que llevas en juego (empiezas con 100)
     y termina la partida ahí.
   - **Disparar** y **fallar** (cartucho vacío) → 😅 dobla los puntos en
     juego, desplaza la bala a otro hueco según un patrón oculto y te da
     una pista sobre dónde está ahora.
   - **Disparar** y **acertar** la bala → 💥 *BOOM*, pierdes todo lo que
     tenías en juego. Ahí acaba la partida (se te dice cuántos días
     sobreviviste).
   - **Marcar** es un farol de bajo riesgo: declaras un hueco "seguro" sin
     disparar. Tienes **3 marcas por partida**; cada uso gasta una, acierte
     o falle. Si aciertas ganas **+50 puntos** sin doblar; si fallas solo
     pierdes la marca — la bala no se mueve y la partida sigue.
3. Las pistas se acumulan turno a turno: compáralas para deducir el patrón
   de movimiento (avanza, retrocede, salta de dos en dos o rebota en
   espejo). Ojo: no siempre son de fiar (ver eventos abajo).
4. De vez en cuando ocurre un **evento aleatorio** tras un disparo:
   - *"Se oye un clic metálico"* → la bala da un paso extra, fuera de su
     patrón habitual.
   - *"El tambor se calienta"* → la siguiente pista **miente** (dice justo
     lo contrario de la verdad), sin avisar cuál fue.

### Ejemplo de partida

```
╔════════════════════════════════════════════╗
║        EL TAMBOR DEL JUICIO         ║
║   Dia 1  (disparo 3/3)  ·  Marcas 1  ║
║   En juego   800 pts                    ║
╚════════════════════════════════════════════╝

   Pistas del tambor:
   #1 La bala esta a la derecha de tu ultimo disparo.
   #2 La bala descansa en un hueco par.

   ┌─┬─┬─┬─┬─┬─┬─┬─┐
   0   0   ·   ·   0   0   0   0
   └─┴─┴─┴─┴─┴─┴─┴─┘
   1  2  3  4  5  6  7  8

   (D)isparar, (R)etirarse o (M)arcar [1]: d
   Elige una posicion (1-8): 5
   Se oye un clic metalico. El tambor se ha movido solo.
   Click. Cartucho vacio. Lo apostado se dobla a 1600 puntos.
   Sobrevives al dia 1.
```

- 💀 Aciertas la bala → **BOOM**, pierdes todo lo apostado (fin de la partida).
- 😅 Fallas un disparo → los puntos en juego se **doblan** y sigues con una
  pista más (y, a veces, un evento).
- 🃏 Marcas un hueco → sin riesgo de muerte: ganas un bono si aciertas,
  solo pierdes la marca si fallas.
- 🏳️ Te retiras cuando quieras y te llevas lo que llevabas en juego.

## 🎮 Versión gráfica (Godot 2D)

Una adaptación visual con el motor **Godot 4.7**, con interfaz completa:
campo de número, botón para disparar y mensaje de resultado en pantalla.

### Cómo jugar

1. Abre Godot e importa el proyecto desde `2d/project.godot`.
2. Pulsa **▶ Play** (o la tecla **F5**).
3. Escribe un número del 1 al 10 (posición del tambor).
4. Pulsa **Enter** o el botón **Disparar**.

En pantalla verás si sobrevives (`Click`) o si te ha tocado la bala (`BOOM`).

### Sistema de 8 rondas

Cada partida tiene 8 rondas. El tambor tiene **10 huecos** y, ronda a ronda,
el número de balas **aumenta** (1, 2, 3, 4, 5, 6, 7 y 8), dejando cada vez
menos huecos vacíos. Sobrevive a las 8 rondas para coronarte como leyenda.

| Ronda | Balas | Vacíos |
|:-----:|:-----:|:------:|
| 1 | 1 | 9 |
| 2 | 2 | 8 |
| 3 | 3 | 7 |
| 4 | 4 | 6 |
| 5 | 5 | 5 |
| 6 | 6 | 4 |
| 7 | 7 | 3 |
| 8 | 8 | 2 |

## 🧰 Herramientas de desarrollo

- **Editor**: cualquiera (VS Code, Neovim, Godot editor...).
- **Control de versiones**: Git.
- **Empaquetado**: `pyproject.toml` con entry point instalable
  (`pip install -e .` deja disponible el comando `ruleta`).
- **Lint y formato**: [ruff](https://docs.astral.sh/ruff/) y
  [black](https://black.readthedocs.io/), configurados en `pyproject.toml`
  (`line-length = 88`, `target-version = "py311"`):

  ```bash
  pip install -e ".[dev]"
  ruff check .
  black --check .
  ```

- **Pruebas y cobertura**: los juegos se pueden verificar desde línea de
  comandos con Godot `--headless` para la versión gráfica, y ejecutando el
  script para la terminal. La versión Python incluye una batería de tests
  por módulo (`terminal/test_*.py`), medida con
  [coverage.py](https://coverage.readthedocs.io/):

  ```bash
  cd terminal && python3 -m unittest discover -s . -v
  # o, con cobertura, desde la raiz del repositorio:
  coverage run -m unittest discover -s terminal && coverage report
  ```

- **Integración continua**: GitHub Actions (`.github/workflows/ci.yml`) corre
  en cada push/PR el lint, el formato, los tests con cobertura (matriz Python
  3.11-3.13) y un smoke test de Godot en modo `--headless`.

## 🧭 Hoja de ruta

### ✅ Hecho en esta beta `v0.1.0`
- [x] Sistema de **8 rondas** con dificultad creciente (1→8 balas) en Godot
- [x] **Lanzadores** para Linux, macOS y Windows (`run.sh`, `run.bat`)
- [x] **Instalador** con acceso directo en el escritorio (`instalar.sh`, `instalar.bat`)
- [x] **Tests** automáticos de la versión Python, con cobertura medida (97%)
- [x] **Empaquetado** con `pyproject.toml` (entry point instalable, config de lint/formato)
- [x] **Integración continua** en GitHub Actions (tests + lint + smoke test de Godot)
- [x] **Lógica separada de la UI** en la versión Godot (estado con señales, sin polling)
- [x] **Feedback visual** por colores en la versión Godot

### 🃏 Rediseño «El Tambor del Juicio» (en marcha)

La versión de terminal está migrando de "elige un número" a un juego de
gestión de riesgo y farol. Fases 1 y 2 (mecánica central y profundidad
estratégica) ya están en la terminal; el resto sigue el orden de este
roadmap:

- [x] **Fase 1 — Terminal:** bala móvil con patrón oculto, pistas veraces y
  apuesta doblar-o-retirarse (`estado.py`, `pistas.py`, `apuestas.py`)
- [ ] **Fase 1 — Godot:** portar la misma mecánica a `RuletaEstado.gd`
- [x] **Fase 2 — Terminal:** farol (marcar huecos, `farol.py`), eventos
  aleatorios que mueven la bala o falsean una pista (`eventos.py`) y
  objetivo de "días de vida" (`estado.dias_sobrevividos`, 3 disparos/día)
- [ ] **Fase 2 — Godot:** portar farol, eventos y días de vida
- [ ] **Fase 3:** ambientación noir/steampunk, tambor animado en Godot y
  colores por estado de hueco en la terminal, historial narrativo al acabar
- [ ] **Fase 4:** multijugador local por turnos, récords/estadísticas y
  opciones de dificultad (huecos y balas iniciales configurables)

### 🎯 Otros próximos pasos
- [ ] Modo «borracho» 🍺 (menos suerte y más humor)
- [ ] Efectos de sonido de gatillo
- [ ] Empaquetado en un ejecutable único (`pyinstaller`)

## 🤝 Cómo contribuir

1. Haz un *fork* del proyecto.
2. Crea una rama: `git checkout -b mi-mejora`.
3. Realiza tus cambios y haz un commit claro.
4. Abre una *pull request*.

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo
[`LICENSE`](LICENSE) para más detalles.

---

<p align="center">
  <em>Hecho para pasar el rato. Si te toca la bala... siempre puedes reiniciar. 🎰</em>
</p>
