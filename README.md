<div align="center">

# 🔫 Russian Roulette 2D

**¿Te sientes con suerte? El tambor está girando y la bala te está esperando.**

Una colección de minijuegos de ruleta rusa construida en diferentes tecnologías:
un clásico de terminal en **Python** y una versión gráfica en **Godot**.

</div>

---

## 🧠 La idea

La mecánica es la eterna apuesta de la ruleta rusa:

1. El revólver tiene **6 huecos** en el tambor.
2. Se coloca **una sola bala** en una posición aleatoria.
3. Tú eliges un número del 1 al 6... y aprietas el gatillo. 🩸

> ⚠️ **Descargo de responsabilidad:** Esto es solo un juego de ficción.
> No existen armas reales de ningún tipo. Solo diversión para la consola y la pantalla.

---

## 📁 Estructura del repositorio

```
.
├── README.md                  ← este archivo
└── juegos/
    ├── python/                ← versión de terminal
    │   └── ruleta.py          ← el juego en Python puro
    └── godot/                 ← versión gráfica 2D
        └── ruleta-rusa-version-uno/
            ├── project.godot  ← proyecto Godot
            ├── MainGame.gd    ← lógica del juego
            └── scenes/        ← escenas de la UI
```

| Carpeta | Tecnología | Qué es |
|---------|-----------|--------|
| `juegos/python` | 🐍 Python 3 | Juego jugado **por terminal** |
| `juegos/godot` | 🎮 Godot 4.6 | Juego **gráfico** con escenas |

---

## 🐍 Versión en Python (terminal)

La versión más pura: abre una terminal, escribe un número y deja que el azar decida.

### Requisitos

- **Python 3.6+** (usa la librería estándar, no necesita nada más)

### Cómo jugar

```bash
cd juegos/python
python3 ruleta.py
```

### Ejemplo de partida

```
=== RULETA RUSA ===
La bala esta en una posicion del 1 al 6.
Elige un numero y cruza los dedos.

Numero del 1 al 6: 4
Click. Solo fue un cartucho vacio. Sobreviviste a la posicion 4 .

Volver a jugar? (s/n):
```

- 💀 Si tu número coincide con la bala: **BOOM. Perdiste.**
- 😅 Si no coincide: **Click. Sobrevives una ronda más.**
- 🔁 Al final puedes volver a jugar tantas veces como quieras.

---

## 🎮 Versión en Godot (gráfica 2D)

Una adaptación visual con motor **Godot 4.6**, donde la lógica vive en
`MainGame.gd` y las escenas en `scenes/`.

### Requisitos

- **Godot 4.6** (edition estándar, con renderizado *GL Compatibility*)

### Cómo jugar

1. Abre Godot e importa el proyecto desde `juegos/godot/ruleta-rusa-version-uno/project.godot`.
2. Ejecuta el proyecto (F5).
3. En la consola del editor, llama a `disparar()` para jugar.

Cada llamada es una ronda:
- Aciertas la bala → 💀 *BOOM*, el tambor se reinicia.
- Sobrevives → avanzas a la siguiente ronda, hasta la 6ª.
- Superas la ronda 6 → 🏆 ganaste la partida.

---

## 🧭 Hoja de ruta

Ideas para próximas versiones:

- [ ] Modo "borracho" 🍺 (límite de suerte y más humor)
- [ ] Múltiples balas en el tambor
- [ ] Selector de dificultad (4, 6 u 8 huecos)
- [ ] Sistema de puntos y récords
- [ ] Versión gráfica completa en Godot con UI interactiva

---

<div align="center">

**Hecho para pasar el rato. Si te toca la bala... siempre puedes reiniciar. 🎰**

</div>
