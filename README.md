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
Escribe un número del 1 al 6..., aprieta el gatillo... y deja que el azar decida.

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

## 🗂️ Estructura del repositorio

```
russian-roulette-2d/
├── README.md            ← esta documentación
├── LICENSE              ← licencia MIT
├── docs/
│   └── GUIA.md          ← guía técnica y de ampliación
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

```bash
cd terminal
python3 ruleta.py
```

> 💡 En Windows usa `python ruleta.py` en lugar de `python3`.

### Ejemplo de partida

```
=== RULETA RUSA ===
La bala esta en una posicion del 1 al 6.
Elige un numero y cruza los dedos.

Numero del 1 al 6: 4
Click. Solo fue un cartucho vacio. Sobreviviste a la posicion 4 .

Volver a jugar? (s/n):
```

- 💀 Si tu número coincide con la bala → **BOOM, perdiste.**
- 😅 Si no coincide → **Click, sobreviviste.**
- 🔁 Puedes volver a jugar tantas veces como quieras.

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
