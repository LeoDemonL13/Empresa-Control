@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title Nexus Obsidian Control - Instalar agente
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
    echo Se necesitan permisos de administrador. Aceptando la ventana que aparece...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b
)

if not exist "%~dp0nexus-agente.exe" (
    echo [X] No se encuentra nexus-agente.exe junto a este archivo.
    echo     Descarga el paquete completo del agente de Windows y vuelve a abrir este archivo.
    goto :fin_error
)

set "SRV=%~1"
set "COD=%~2"

if "!SRV!"=="" set /p "SRV=Direccion del servidor (ej. https://nexus.miempresa.com): "
if "!SRV!"=="" goto :faltan
if "!COD!"=="" set /p "COD=Codigo de enrolamiento del panel (Equipos - Agregar equipo): "
if "!COD!"=="" goto :faltan

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalador\instalar.ps1" -Servidor "!SRV!" -Codigo "!COD!" -Origen "%~dp0nexus-agente.exe"
if errorlevel 1 goto :fin_error

echo.
echo Listo. El equipo debe aparecer "En linea" en el panel en menos de un minuto.
pause
exit /b 0

:faltan
echo [X] Faltan datos. Vuelve a abrir este archivo y escribe la direccion y el codigo.
goto :fin_error

:fin_error
echo.
pause
exit /b 1
