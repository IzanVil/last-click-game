#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

RUTA_RAIZ="$(cd "$(dirname "$0")" && pwd)"
TERMINAL_DIR="terminal"
PY=""

if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "ERROR: No se encontro Python."
    echo "Instala Python 3.11 o superior desde python.org"
    echo "y vuelve a ejecutar este instalador."
    exit 1
fi

echo "Se detecto Python: ${PY} ($(${PY} --version 2>&1))"

MAYOR=$("${PY}" -c "import sys; print(sys.version_info.major)")
MENOR=$("${PY}" -c "import sys; print(sys.version_info.minor)")
if [ "$MAYOR" -lt 3 ] || { [ "$MAYOR" -eq 3 ] && [ "$MENOR" -lt 11 ]; }; then
    echo "ERROR: Necesitas Python 3.11 o superior (el sistema tiene ${MAYOR}.${MENOR})."
    exit 1
fi

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
    cat > "$ESC/TamborDelJuicio.desktop" <<EOF
[Desktop Entry]
Name=El Tambor del Juicio
Comment=Juego de deduccion y riesgo en terminal
Exec=${RUTA_RAIZ}/run.sh
Icon=${RUTA_RAIZ}/2d/icon.svg
Terminal=true
Type=Application
Categories=Game;
EOF
    chmod +x "$ESC/TamborDelJuicio.desktop"
    echo "Acceso directo creado en: $ESC/TamborDelJuicio.desktop"
    if [ -e "$ESC/RussianRoulette.desktop" ]; then
        echo "Aviso: quedo el acceso directo antiguo en $ESC/RussianRoulette.desktop"
        echo "       Apunta al mismo run.sh y sigue funcionando; puedes borrarlo."
    fi
else
    echo "Aviso: no se detecto escritorio, no se creo acceso directo."
fi

if [ "$INSTALAR_DIRTO" = "1" ]; then
    echo "Abriendo El Tambor del Juicio..."
    exec "${PY}" "${TERMINAL_DIR}/ruleta.py"
fi

echo ""
echo "Instalacion completada. Para jugar: ./run.sh"
