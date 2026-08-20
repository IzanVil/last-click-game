<p align="center">
  <img src="2d/icon.svg" alt="Russian Roulette" width="120">
</p>

<h1 align="center">🔫 Russian Roulette</h1>

<p align="center">
  <strong>¿Te sientes con suerte? El tambor gira y la bala te está esperando.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Godot-4.6%2B-478CBF?logo=godotengine&logoColor=white" alt="Godot">
  <img src="https://img.shields.io/badge/estado-en%20desarrollo-yellow" alt="Estado">
  <img src="https://img.shields.io/badge/licencia-MIT-green" alt="Licencia">
</p>

---

Una colección de minijuegos de ruleta rusa en **dos sabores**: un clásico de
**terminal** escrito en Python y una versión **gráfica 2D** hecha con Godot.
Elige una posición del tambor aprieta el gatillo y deja que el azar decida.

## 🧠 La idea

La eterna apuesta de la ruleta rusa, llevada a la consola y a la pantalla:

1. El tambor tiene **10 huecos**, cargados con un número variable de balas.
2. El jugador elige una posición del tambor y **aprieta el gatillo**.
3. Si el hueco es una bala → 💥 *BOOM* (pierde). Si está vacío → 😅 *Click* (sobrevive).
4. En la versión gráfica cada **ronda añade más balas**, subiendo la tensión hasta el final.

> ⚠️ **Descargo de responsabilidad:** es solo un juego de ficción. No existe
> ninguna arma real. Solo diversión para la terminal y la pantalla.

## 📦 Requisitos

| Versión | Tecnología | Requisito |
|---------|-----------|-----------|
| Terminal | 🐍 Python | Python 3.6 o superior |
| Gráfica  | 🎮 Godot | Godot 4.6 o superior |

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
├── run.sh               ← lanzador Linux / macOS
├── run.bat              ← lanzador Windows
├── terminal/            ← versión de consola
│   └── ruleta.py        ← juego en Python puro
└── 2d/                  ← versión gráfica
    ├── project.godot    ← proyecto Godot
    ├── MainGame.gd      ← lógica del juego
    ├── scenes/          ← escenas (UI)
    └── assets/          ← recursos visuales
```

## 🐍 versión de terminal (Python)

La versión más pura: abre una terminal, escribe un número y deja que el azar decida.

### Cómo jugar

Desde la raíz del repositorio:

```bash
./run.sh                       # usa el lanzador (Linux / macOS)
# o directamente:
cd terminal && python3 ruleta.py
```

> 💡 En Windows usa `run.bat`, o `python ruleta.py` en lugar de `python3`.

### Ejemplo de partida

```
 ╔════════════════════════════════════════════╗
 ║            RULETA RUSA              ║
 ║   Ronda 3/8  ·  Balas 3  ·  Vacios 7    ║
 ╚════════════════════════════════════════════╝

   La bala descansa en un hueco. Tu huella deja marcas.
   ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
   0  0  0  0  0  0  0  0  0  0
   1  2  3  4  5  6  7  8  9  10

   Elige una posicion (1-10): 4
   Click. Cartucho vacio. Avanzas a la ronda 4.
```

- 💀 Si eliges un hueco con bala → **BOOM, pierdes.**
- 😅 Si eliges un hueco vacío → **Click, avanzas a la siguiente ronda.**
- 🏆 Sobrevive a las 8 rondas para ganar.

## 🎮 versión gráfica (Godot 2D)

Una adaptación visual con el motor **Godot 4.6**, con interfaz completa:
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
- **Pruebas**: los juegos se pueden verificar desde línea de comandos con Godot
  `--headless` para la versión gráfica, y ejecutando el script para la terminal.

## 🧭 Hoja de ruta

- [ ] Modo «borracho» 🍺 (menos suerte y más humor)
- [ ] Múltiples balas en el tambor
- [ ] Selector de dificultad (tambores de 4, 6 u 8 huecos)
- [ ] Sistema de puntos, rachas y récords
- [ ] Efectos de sonido de gatillo
- [ ] Animación del tambor girando

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
