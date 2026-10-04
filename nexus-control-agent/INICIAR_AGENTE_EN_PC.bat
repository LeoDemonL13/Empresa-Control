@echo off
setlocal EnableExtensions
title Nexus Obsidian Control - Agente
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [X] No se encontro Python.
    echo     Instala Python 3.11 o superior: https://www.python.org/downloads/
    goto :fin_error
)

if not exist ".venv" (
    echo [..] Preparando el agente. Solo se hace la primera vez.
    python -m venv .venv
    if errorlevel 1 goto :fin_error
)

call ".venv\Scripts\activate.bat"

python -m pip install --quiet --disable-pip-version-check --upgrade pip
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo [X] No se pudieron instalar las dependencias del agente.
    echo     Revisa tu conexion a internet y vuelve a abrir este archivo.
    goto :fin_error
)

echo.
echo  ==================================================
echo    NEXUS OBSIDIAN CONTROL - Agente
echo  ==================================================
echo.
echo  La primera vez te pide la direccion del servidor y el
echo  codigo de enrolamiento que generaste en el panel, en
echo  Equipos - Agregar equipo. Las siguientes veces arranca
echo  solo.
echo.
echo  Para detener el agente: Ctrl+C o cierra esta ventana.
echo  ==================================================
echo.

python main.py

echo.
echo El agente se detuvo.
pause
exit /b 0

:fin_error
echo.
echo Presiona una tecla para cerrar esta ventana.
pause >nul
exit /b 1
