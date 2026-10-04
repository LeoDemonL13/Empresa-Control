@echo off
setlocal EnableExtensions
title Nexus Obsidian Control - Detener
cd /d "%~dp0"

set "API=%~dp0nexus-control-api"

where docker >nul 2>&1
if errorlevel 1 goto :sin_docker

docker info >nul 2>&1
if errorlevel 1 goto :sin_docker

docker compose --project-directory "%API%" -f "%API%\docker-compose.yml" stop
echo.
echo Servidor detenido. Los datos se conservan.
echo Para volver a iniciar abre INICIAR_EN_PC.bat
echo.
pause
exit /b 0

:sin_docker
echo.
echo Docker no esta en ejecucion. No hay nada que detener.
echo.
pause
exit /b 0
