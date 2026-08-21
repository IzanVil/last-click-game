#!/usr/bin/env bash
# Lanzador del juego de ruleta rusa (versión terminal Python)
# Uso:
#   ./run.sh            -> juega a la ruleta rusa en la terminal
#   ./run.sh -g         -> abre el proyecto en el editor Godot
set -euo pipefail

cd "$(dirname "$0")"

MODO="$(pwd)"
TERMINAL_DIR="terminal"

if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "No se encontro Python. Instala Python 3.11 o superior." >&2
    exit 1
fi

case "${1:-}" in
    -g|--godot)
        echo "Abriendo el proyecto en el editor Godot (2d/)..."
        if command -v godot >/dev/null 2>&1; then
            godot --path "2d" --editor
        elif command -v godot4 >/dev/null 2>&1; then
            godot4 --path "2d" --editor
        else
            echo "Godot no esta en el PATH. Abre 2d/project.godot manualmente." >&2
        fi
        ;;
    *)
        echo "Lanzando Russian Roulette (terminal)..."
        "$PYTHON" "${TERMINAL_DIR}/ruleta.py"
        ;;
esac
