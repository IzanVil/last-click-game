@echo off
rem ---------------------------------------------------------------
rem Instalador de Russian Roulette (version terminal Python) para Windows
rem Uso: doble click en este archivo, o desde CMD:
rem   instalar.bat          -> instala y ejecuta el juego
rem   instalar.bat --solo   -> solo instala (sin abrir el juego)
rem ---------------------------------------------------------------
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo Verificando Python...

set "PY="
where python >nul 2>&1
if %errorlevel%==0 (
    set "PY=python"
) else (
    where python3 >nul 2>&1
    if %errorlevel%==0 (
        set "PY=python3"
    ) else (
        echo.
        echo ERROR: No se encontro Python.
        echo Instala Python 3.11 o superior desde python.org
        echo y vuelve a ejecutar este instalador.
        pause
        exit /b 1
    )
)

%PY% -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Necesitas Python 3.11 o superior.
    pause
    exit /b 1
)

echo Se detecto: %PY%

if /i "%~1"=="--solo" goto :fin

echo Abriendo Russian Roulette...
%PY% terminal\ruleta.py
goto :eof

:fin
echo.
echo Instalacion completada. Para jugar: run.bat
pause
