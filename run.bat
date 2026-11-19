@echo off
setlocal
cd /d "%~dp0"

if /i "%~1"=="-g" goto :godot
if /i "%~1"=="--godot" goto :godot

where python >nul 2>nul
if errorlevel 1 (
    echo No se encontro python. Asegurate de que este en el PATH.
    goto :eof
)

echo Lanzando El Tambor del Juicio (terminal)...
python terminal\ruleta.py %*
goto :eof

:godot
echo Abriendo el proyecto en el editor Godot (2d\project.godot)...
start "" godot --path "2d" --editor 2>nul || start "" 2d\project.godot
goto :eof
