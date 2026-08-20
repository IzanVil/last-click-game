#!/usr/bin/env bash
# ---------------------------------------------------------------
# Instalador de Russian Roulette (version terminal Python)
# Uso:
#   ./instalar.sh          -> instala y ejecuta el juego
#   ./instalar.sh --solo   -> instala sin abrir el juego de golpe
# Prerequisito: Python 3.6+ instalado en el sistema.
# ---------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")"

RUTA_RAIZ="$(cd "$(dirname "$0")" && pwd)"
TERMINAL_DIR="terminal"
PY=""

# --- 1. Localizar Python -------------------------------------------
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "ERROR: No se encontro Python."
    echo "Instala Python 3.6 o superior desde python.org"
    echo "y vuelve a ejecutar este instalador."
    exit 1
fi

echo "Se detecto Python: ${PY} ($(${PY} --version 2>&1))"

# --- 2. Verificar la version ----------------------------------------
MAYOR=$("${PY}" -c "import sys; print(sys.version_info.major)")
MENOR=$("${PY}" -c "import sys; print(sys.version_info.minor)")
if [ "$MAYOR" -lt 3 ] || { [ "$MAYOR" -eq 3 ] && [ "$MENOR" -lt 6 ]; }; then
    echo "ERROR: Necesitas Python 3.6 o superior (el sistema tiene 3.${MENOR})."
    exit 1
fi

# --- 3. Crear acceso directo (solo en Linux/macOS) ------------------
INSTALAR_DIRTO=1
if [ "${1:-}" = "--solo" ]; then
    INSTALAR_DIRTO=0
fi

    ESC=""
if [ "$INSTALAR_DIRTO" = "1" ]; then
    if [ -d "$HOME/Desktop" ]; then
        ESC="$HOME/Desktop"
    elif [ -d "$HOME/Escritorio" ]; then
        ESC="$HOME/Escritorio"
    elif [ -d "$HOME/OneDrive/Escritorio" ]; then
        ESC="$HOME/OneDrive/Escritorio"
    fi
fi

if [ -n "$ESC" ]; then
    cat > "$ESC/RussianRoulette.desktop" <<EOF
[Desktop Entry]
Name=Russian Roulette
Comment=Juego de ruleta rusa en terminal
Exec=${RUTA_RAIZ}/run.sh
Icon=${RUTA_RAIZ}/2d/icon.svg
Terminal=true
Type=Application
Categories=Game;
EOF
    chmod +x "$ESC/RussianRoulette.desktop"
    echo "Acceso directo creado en: $ESC/RussianRoulette.desktop"
else
    echo "Aviso: no se detecto escritorio, no se creo acceso directo."
fi

# --- 4. Lanzar el juego ---------------------------------------------
if [ "$INSTALAR_DIRTO" = "1" ]; then
    echo "Abriendo Russian Roulette..."
    exec "${PY}" "${TERMINAL_DIR}/ruleta.py"
fi

echo ""
echo "Instalacion completada. Para jugar: ./run.sh"
