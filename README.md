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
Desde esta beta, las dos versiones juegan **la misma mecánica**:
**El Tambor del Juicio**, un rediseño centrado en la gestión de riesgo y el
farol (ver [Hoja de ruta](#hoja-de-ruta) para el detalle fase a fase).

## 🧠 La idea

El tambor tiene **8 huecos** y una única bala que **se desplaza** tras cada
disparo que la falla, siguiendo un patrón oculto que debes deducir a partir
de las pistas (a veces mentirosas) y de eventos aleatorios. En cada turno
decides: **te retiras** con los puntos que llevas en juego, **disparas**
arriesgando que se **doblen** (o perderlo todo), o gastas una de tus 3
**marcas** para declarar un hueco seguro sin arriesgar el pellejo. El
objetivo no es una única partida: es acumular **días de vida**.

- **🐍 Terminal** — interfaz de teclado y colores ANSI en un tambor ASCII.
- **🎮 Gráfica (Godot)** — misma mecánica con tambor animado, sonido y una
  ambientación noir/steampunk (metal envejecido, latón, tipografía de
  máquina de escribir y vibración de pantalla al morir).

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

# Con dificultad personalizada (reenvía los argumentos a ruleta.py)
./run.sh --huecos 6

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
│   ├── historial.py     ← contadores de la partida y resumen narrativo
│   ├── records.py       ← récords persistidos en ~/.tambor_del_juicio/
│   └── test_*.py        ← pruebas unitarias de los ocho módulos
└── 2d/                  ← versión gráfica: El Tambor del Juicio
    ├── project.godot    ← proyecto Godot
    ├── RuletaEstado.gd  ← orquestador: conecta la lógica y emite señales
    ├── TamborJuicio.gd  ← tambor y bala: posición, patrón, días de vida
    ├── Pistas.gd        ← generación de pistas (veraces o mentirosas)
    ├── Apuesta.gd       ← apuesta doblar-o-retirarse
    ├── Farol.gd         ← marcar un hueco como seguro sin disparar
    ├── Eventos.gd       ← eventos aleatorios (clic metálico, tambor caliente)
    ├── Historial.gd     ← contadores de la partida y resumen narrativo
    ├── Jugador.gd       ← apuesta/marcas/disparos de un jugador y desempate
    ├── Dificultad.gd    ← presets fácil/normal/difícil
    ├── Records.gd       ← récords persistidos en user://records.json
    ├── MainGame.gd      ← vista: menú, Label/Button/Tween
    ├── TamborView.gd    ← dibuja el tambor y sus animaciones
    ├── tests/           ← scripts headless (lógica + integración de escena)
    ├── scenes/          ← escenas (UI)
    └── assets/          ← audio, y las fuentes de máquina de escribir
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
5. El tambor ASCII colorea cada hueco con lo que sabes de él:
   - 🟡 **amarillo** `?` — candidato: cumple con **todas** las pistas
     vigentes (se cruzan entre sí). Si de repente no queda ninguno en
     amarillo, alguna pista reciente no encajaba... quizá te mintieron.
   - 🟢 **verde** `✓` / 🔴 **rojo** `✗` — resultado de un farol: confirmaste
     que ahí no había bala, o que sí la había, en ese momento.
   - ⚪ **gris** `·` — ya disparaste ahí alguna vez.
6. Al terminar la partida (mueras o te retires) se muestra un resumen
   narrativo de lo que ha pasado: días sobrevividos, faroles lanzados y
   acertados, y eventos que sufriste.

### Dificultad personalizada

Tres presets (`--dificultad facil|normal|dificil`) ajustan a la vez el
tamaño del tambor y las marcas de farol por partida; `--huecos`/`--marcas`
sueltos afinan cualquiera de los dos por separado (y pisan al preset si
se combinan con él):

| Dificultad | Huecos | Marcas |
|:----------:|:------:|:------:|
| `facil`    | 10     | 4      |
| `normal` (por defecto) | 8 | 3 |
| `dificil`  | 6      | 2      |

```bash
cd terminal && python3 ruleta.py --dificultad dificil
python3 ruleta.py --huecos 6 --marcas 1   # a medida, sin usar un preset
python3 ruleta.py --help       # ver todas las opciones
python3 ruleta.py --version    # version instalada (o aviso si se ejecuta sin instalar)
```

> 💡 Con `pip install -e .` el comando instalado es `ruleta`, con las mismas
> opciones (`ruleta --dificultad dificil`).

### Récords

Cada partida (en solitario o en un duelo) actualiza un fichero de récords
en `~/.tambor_del_juicio/records.json`: días máximos sobrevividos, puntos
máximos en una partida, partidas jugadas y faroles acertados/usados.
Se guarda solo, y `--records` los muestra sin jugar:

```bash
python3 ruleta.py --records
```

Si superas tu récord de días, la pantalla final de esa partida lo anuncia.

### Modo duelo

`--duelo` enfrenta a dos jugadores por turnos **en el mismo tambor**: la
bala, su patrón y las pistas acumuladas son compartidas (es literalmente
el mismo revólver), pero cada jugador tiene su propia apuesta y sus
propias marcas de farol. La partida termina en cuanto el turno de uno de
los dos acaba en **BOOM** o en retirada — el otro no sigue jugando después
— y gana quien haya sobrevivido más días (en caso de empate, quien tenga
más puntos):

```bash
python3 ruleta.py --duelo
python3 ruleta.py --duelo --dificultad facil   # combinable con dificultad
```

### Ejemplo de partida

```
╔════════════════════════════════════════════╗
║        EL TAMBOR DEL JUICIO         ║
║   Dia 2  (disparo 1/3)  ·  Marcas 2  ║
║   En juego   900 pts                    ║
╚════════════════════════════════════════════╝

   Pistas del tambor:
   #1 La bala esta en la mitad derecha del tambor.
   #2 La bala no esta en los huecos pares.
   #3 La bala no esta en los huecos pares.

   ┌─┬─┬─┬─┬─┬─┬─┬─┐
   ·   ·   ·   0   ?   0   ✓   0
   └─┴─┴─┴─┴─┴─┴─┴─┘
   1  2  3  4  5  6  7  8

   (D)isparar, (R)etirarse o (M)arcar [2]: r

    ✦  TE RETIRAS A TIEMPO  ✦

   Cobras 900 puntos tras 3 disparo(s) (1 dia(s) sobrevivido(s)).
   Hoy sobreviviste 1 dia y faroleaste 1 vez (1 acertado).
```

En este tambor de 8, cruzar "mitad derecha" (5-8) con "no par" (1,3,5,7) deja
solo el 5 y el 7 como candidatos (amarillo `?`); el 7 ya se marcó y salió
seguro (verde `✓`); el 1, 2 y 3 son huecos por los que ya se disparó (gris `·`).

- 💀 Aciertas la bala → **BOOM**, pierdes todo lo apostado (fin de la partida).
- 😅 Fallas un disparo → los puntos en juego se **doblan** y sigues con una
  pista más (y, a veces, un evento).
- 🃏 Marcas un hueco → sin riesgo de muerte: ganas un bono si aciertas,
  solo pierdes la marca si fallas.
- 🏳️ Te retiras cuando quieras y te llevas lo que llevabas en juego.

## 🎮 Versión gráfica (Godot 2D) — El Tambor del Juicio

La versión gráfica juega **la misma mecánica que la terminal** (las
cuatro fases del rediseño): tambor de bala móvil, pistas, apuesta
doblar-o-retirarse, farol, días de vida, dificultad, récords y modo
duelo — con ambientación noir/steampunk, tipografía de máquina de
escribir, tambor animado y vibración en pantalla al morir.

### Cómo jugar

1. Abre Godot e importa el proyecto desde `2d/project.godot`.
2. Pulsa **▶ Play** (o la tecla **F5**).
3. En el **menú** eliges dificultad y, si quieres, marcas *Modo duelo* y
   pones los nombres de los dos jugadores. Pulsa **Empezar**.
4. Escribe una posición del tambor y pulsa **Enter** o uno de los tres
   botones: **Disparar**, **Marcar** o **Retirarse** (las mismas
   acciones que en la terminal, ver [Reglas](#reglas) más arriba).

El tambor se colorea igual que en la terminal: 🟡 amarillo = candidato
según las pistas vigentes, 🟢 verde / 🔴 rojo = resultado de un farol, ⚪
gris = ya disparado.

Donde la terminal usa opciones de línea de comandos (`--dificultad`,
`--duelo`, `--records`), aquí están en ese menú previo, que además
muestra los récords; y donde la terminal vuelve al prompt al terminar
una partida, aquí se vuelve al menú con los récords ya actualizados.
Los récords se guardan en `user://records.json` (el equivalente
idiomático en Godot de `~/.tambor_del_juicio/records.json`).

### Arquitectura: lógica pura + señales, igual que en Python

`2d/RuletaEstado.gd` orquesta `TamborJuicio.gd`, `Apuesta.gd`, `Farol.gd`,
`Eventos.gd`, `Historial.gd` y `Jugador.gd` — sin conocer nodos ni UI, ni
tocar disco, igual que `terminal/estado.py` y compañía — y emite señales
(`disparo_sobrevivido`, `pista_nueva`, `evento_ocurrido`,
`farol_resuelto`, `dia_completado`, `impacto`, `retirada`,
`turno_cambiado`, `duelo_terminado`...) que `MainGame.gd` escucha para
actualizar Label/Button/Tween. `TamborView.gd` solo sabe pintar el estado
que le pasa `MainGame.gd`, sin conocer ninguna regla del juego.

Una partida en solitario es, internamente, **un duelo de un solo
jugador**: los dos modos comparten la misma lógica de turnos
(`RuletaEstado.jugadores` y `turno`), y los atajos `apuesta`/`farol`/
`historial`/`disparos` apuntan siempre al jugador activo.

### Tests

Godot no trae un framework de tests instalado en el proyecto (ni
[GUT](https://github.com/bitwes/Gut) ni similar); en su lugar hay dos
scripts headless en `2d/tests/`, a modo de arnés mínimo:

```bash
cd 2d
godot --headless --script res://tests/test_logica.gd --path .    # RuletaEstado y sus módulos, sin nodos
godot --headless --script res://tests/test_escena.gd --path .    # MainGame.tscn real: menú, disparo, farol, duelo
```

Ambos salen con exit code 0 si todo pasa, 1 si algo falla (y lo imprime);
la CI (`godot-smoke-test`) los ejecuta en cada push/PR, junto al
`--check-only` que ya había. Los tests que tocan récords escriben en un
archivo aparte y lo borran al terminar, así que **no pisan los récords
de quien los ejecuta**.

## 🧰 Herramientas de desarrollo

- **Editor**: cualquiera (VS Code, Neovim, Godot editor...).
- **Control de versiones**: Git.
- **Empaquetado**: `pyproject.toml` con entry point instalable
  (`pip install -e .` deja disponible el comando `ruleta`).
- **Lint, formato y tipos**: [ruff](https://docs.astral.sh/ruff/),
  [black](https://black.readthedocs.io/) y [mypy](https://mypy.readthedocs.io/),
  configurados en `pyproject.toml` (`line-length = 88`,
  `target-version = "py311"`, `disallow_untyped_defs` para `ruleta.py`):

  ```bash
  pip install -e ".[dev]"
  ruff check .
  black --check .
  mypy
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
- [x] **El Tambor del Juicio** en las dos versiones (terminal y Godot):
  bala móvil, pistas, apuesta doblar-o-retirarse, farol, eventos y días
  de vida — ver el detalle fase a fase más abajo
- [x] **Lanzadores** para Linux, macOS y Windows (`run.sh`, `run.bat`)
- [x] **Instalador** con acceso directo en el escritorio (`instalar.sh`, `instalar.bat`)
- [x] **Tests** automáticos de la versión Python (97% de cobertura) y dos
  scripts headless para la versión Godot (lógica + integración de escena)
- [x] **Empaquetado** con `pyproject.toml` (entry point instalable, config de lint/formato/tipos)
- [x] **Integración continua** en GitHub Actions (tests + lint + tipos de
  Python, `--check-only` + tests headless de Godot)
- [x] **Lógica separada de la UI** en ambas versiones (estado con señales
  o retorno de valores, sin polling)
- [x] **Feedback visual** por colores en la versión Godot, ahora también
  por estado de hueco (paleta noir/steampunk)
- [x] **Selector de dificultad** en ambas versiones (presets
  fácil/normal/difícil: por CLI en la terminal, en el menú en Godot)
- [x] **Récords persistidos** entre partidas y **modo duelo** local por
  turnos con el tambor compartido, también en ambas versiones
- [x] **Efectos de sonido** de disparo, victoria y derrota (versión Godot)
- [x] **Animación del tambor** — giro al empezar partida, tensión antes de
  revelar un disparo o farol, y vibración de pantalla al morir (Godot)

### 🃏 Rediseño «El Tambor del Juicio»

Las dos versiones migraron de "elige un número" a un juego de gestión de
riesgo y farol, y ya juegan **la misma mecánica** (Fases 1-3 completas en
ambas):

- [x] **Fase 1 — Terminal:** bala móvil con patrón oculto, pistas veraces y
  apuesta doblar-o-retirarse (`estado.py`, `pistas.py`, `apuestas.py`)
- [x] **Fase 1 — Godot:** la misma mecánica en `TamborJuicio.gd`,
  `Pistas.gd` y `Apuesta.gd`, orquestados por `RuletaEstado.gd`
- [x] **Fase 2 — Terminal:** farol (marcar huecos, `farol.py`), eventos
  aleatorios que mueven la bala o falsean una pista (`eventos.py`) y
  objetivo de "días de vida" (`estado.dias_sobrevividos`, 3 disparos/día)
- [x] **Fase 2 — Godot:** lo mismo en `Farol.gd`, `Eventos.gd` y
  `RuletaEstado.dias_sobrevividos()`, con botón de Marcar en la UI
- [x] **Fase 3 — Terminal:** tambor coloreado por estado de hueco (verde
  seguro / rojo peligro / amarillo candidato según el cruce de pistas
  vigentes / gris ya disparado, `pistas.interseccion`) e historial
  narrativo al terminar la partida (`historial.py`)
- [x] **Fase 3 — Godot:** mismos cuatro colores en `TamborView.gd` (paleta
  noir/steampunk: metal envejecido y laton en vez de rojo/verde "de
  manual"), vibración de pantalla al morir, `Historial.gd` con el mismo
  resumen narrativo y **tipografía de máquina de escribir** (Courier Prime
  en toda la interfaz, Special Elite en el título)
- [x] **Fase 4 — Terminal:** opciones de dificultad por preset
  (`--dificultad facil|normal|dificil`, o `--huecos`/`--marcas` sueltos),
  récords persistidos entre partidas (`records.py`,
  `~/.tambor_del_juicio/records.json`, con aviso de "nuevo récord" en la
  pantalla final) y modo duelo local por turnos (`--duelo`,
  `jugar_duelo()`): mismo tambor/pistas compartidos, apuesta y marcas
  propias de cada jugador, termina en el primer BOOM o retirada
- [x] **Fase 4 — Godot:** lo mismo, en un menú previo a la partida en vez
  de por CLI: `Dificultad.gd` (mismos tres presets), `Records.gd`
  (`user://records.json`, con aviso de "nuevo récord") y duelo local por
  turnos con `Jugador.gd` + `RuletaEstado.jugadores`/`turno` — donde una
  partida en solitario es, internamente, un duelo de un solo jugador

Con eso, **las cuatro fases del rediseño están completas en las dos
versiones**.

### 🎯 Otros próximos pasos
- [ ] Modo «borracho» 🍺 (menos suerte y más humor)
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
