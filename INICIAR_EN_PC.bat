@echo off
setlocal EnableExtensions
title Nexus Obsidian Control - Inicio
cd /d "%~dp0"

set "API=%~dp0nexus-control-api"
set "FRONT=%~dp0nexus-control-frontend"
set "URL_API=http://localhost:5001/health"
set "URL_APP=http://localhost:5173"
set "DC=docker compose --project-directory "%API%" -f "%API%\docker-compose.yml""
set "LOGTMP=%TEMP%\nexus_control_api_log.txt"

echo.
echo  ==================================================
echo    NEXUS OBSIDIAN CONTROL  -  Inicio rapido
echo  ==================================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
    echo [X] No se encontro Docker.
    echo     Instala Docker Desktop: https://www.docker.com/products/docker-desktop/
    goto :fin_error
)

where node >nul 2>&1
if errorlevel 1 (
    echo [X] No se encontro Node.js.
    echo     Instala la version 22 LTS: https://nodejs.org/
    goto :fin_error
)

docker info >nul 2>&1
if not errorlevel 1 goto :docker_listo

echo [..] Docker no esta en ejecucion. Abriendo Docker Desktop...
if not exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" goto :docker_manual
start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a espera=0

:esperar_docker
timeout /t 3 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto :docker_listo
set /a espera+=3
if %espera% GEQ 180 goto :docker_manual
goto :esperar_docker

:docker_manual
echo [X] Docker no responde.
echo     Abre Docker Desktop, espera a que indique que esta en ejecucion
echo     y vuelve a abrir este archivo.
goto :fin_error

:docker_listo
echo [OK] Docker listo.

if exist "%API%\.env" goto :env_listo
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\preparar_entorno.ps1"
if errorlevel 1 goto :fin_error

:env_listo
echo [..] Levantando el servidor: API, base de datos y Redis.
echo      La primera vez tarda varios minutos.
echo.
%DC% up -d --build
if errorlevel 1 goto :error_compose

set /a espera=0
echo.
echo [..] Esperando a que el servidor responda...

:esperar_api
curl.exe -fs "%URL_API%" >nul 2>&1
if not errorlevel 1 goto :api_lista
for /f %%i in ('%DC% ps -a -q --status exited api 2^>nul') do goto :api_caida
set /a espera+=2
if %espera% GEQ 150 goto :api_no_responde
timeout /t 2 /nobreak >nul
goto :esperar_api

:api_caida
%DC% logs --tail 60 api > "%LOGTMP%" 2>&1
findstr /c:"password authentication failed" "%LOGTMP%" >nul
if not errorlevel 1 goto :password_desincronizada

echo.
echo [X] El servidor se detuvo al arrancar. Ultimos mensajes:
echo.
type "%LOGTMP%"
goto :fin_error

:password_desincronizada
echo.
echo [X] La base de datos ya existia, creada con una contrasena distinta
echo     a la de tu archivo .env actual.
echo.
echo     Esto pasa si antes abriste el proyecto desde otra carpeta o copia.
echo     Para corregirlo hay que borrar esa base de datos anterior y crearla
echo     de nuevo. Todavia no hay informacion importante guardada.
echo.
set "confirmar="
set /p "confirmar=Borrar la base de datos anterior y reintentar? (S/N): "
if /i not "%confirmar%"=="S" goto :fin_error

echo.
echo [..] Borrando la base de datos anterior...
%DC% down -v
if errorlevel 1 goto :fin_error
echo [OK] Lista. Reintentando...
echo.
goto :env_listo

:api_no_responde
echo.
echo [X] El servidor no respondio a tiempo. Ultimos mensajes:
echo.
%DC% logs --tail 40 api
goto :fin_error

:error_compose
echo.
echo [X] Docker no pudo levantar el servidor. Revisa los mensajes de arriba.
goto :fin_error

:api_lista
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\preparar_entorno.ps1" -Finalizar
echo [OK] Servidor listo en http://localhost:5001

if exist "%FRONT%\node_modules" goto :front_listo
echo [..] Instalando dependencias del panel. Solo se hace la primera vez.
pushd "%FRONT%"
call npm ci --no-audit --no-fund
set "codigo=%errorlevel%"
popd
if not "%codigo%"=="0" goto :error_npm

:front_listo
echo.
echo  --------------------------------------------------
echo    Panel:     %URL_APP%
echo    Servidor:  %URL_API%
echo  --------------------------------------------------
echo    Para cerrar el panel: Ctrl+C o cierra esta ventana.
echo    Para apagar el servidor de fondo: DETENER_EN_PC.bat
echo  --------------------------------------------------
echo.

start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 4; Start-Process '%URL_APP%'"

pushd "%FRONT%"
call npm run dev -- --strictPort
popd

echo.
echo El panel se cerro. El servidor sigue activo en segundo plano.
echo Para apagarlo abre DETENER_EN_PC.bat
pause
exit /b 0

:error_npm
echo.
echo [X] No se pudieron instalar las dependencias del panel.
echo     Revisa tu conexion a internet y vuelve a abrir este archivo.
goto :fin_error

:fin_error
echo.
echo Presiona una tecla para cerrar esta ventana.
pause >nul
exit /b 1
