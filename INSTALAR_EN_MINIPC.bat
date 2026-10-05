@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title Nexus Obsidian Control - Instalacion en Mini PC

echo.
echo ============================================================
echo   Instalacion de Nexus en el Mini PC (Ubuntu Server)
echo ============================================================
echo.
echo Requisitos previos:
echo   - Ubuntu Server 24.04 instalado en el Mini PC, con OpenSSH activado.
echo   - El Mini PC conectado por cable a internet.
echo   - Un tunel de Cloudflare creado (ver GUIA_MINI_PC.md, seccion 4.2).
echo   - Las imagenes publicadas en GitHub (ver GUIA_MINI_PC.md, seccion 4.1).
echo.

where ssh >nul 2>&1
if errorlevel 1 goto :sin_ssh
where scp >nul 2>&1
if errorlevel 1 goto :sin_ssh

if not exist "%~dp0deploy\appliance\provision.sh" (
    echo ERROR: no se encuentra deploy\appliance\provision.sh junto a este archivo.
    goto :fin_error
)

set "MP_IP="
set "MP_USER="
set "NEXUS_DOMAIN="
set "GHCR_OWNER="
set "CLOUDFLARE_TUNNEL_TOKEN="
set "GHCR_USER="
set "GHCR_TOKEN="
set "TAILSCALE_AUTHKEY="
set "HEARTBEAT_URL="
set "ALERT_WEBHOOK_URL="
set "SUPERADMIN_USERNAME="
set "TZ_LOCAL="

set /p "MP_IP=Direccion IP del Mini PC en tu red (ej. 192.168.1.50): "
if "!MP_IP!"=="" goto :faltan_datos
set /p "MP_USER=Usuario SSH del Mini PC (ej. admin): "
if "!MP_USER!"=="" goto :faltan_datos
set /p "NEXUS_DOMAIN=Dominio publico (ej. nexus.miempresa.com, sin https://): "
if "!NEXUS_DOMAIN!"=="" goto :faltan_datos
set /p "GHCR_OWNER=Usuario u organizacion de GitHub duena del repositorio: "
if "!GHCR_OWNER!"=="" goto :faltan_datos
set /p "CLOUDFLARE_TUNNEL_TOKEN=Token del tunel de Cloudflare: "
if "!CLOUDFLARE_TUNNEL_TOKEN!"=="" goto :faltan_datos
set /p "SUPERADMIN_USERNAME=Correo/usuario del super administrador de Nexus: "
if "!SUPERADMIN_USERNAME!"=="" goto :faltan_datos
set /p "GHCR_USER=Usuario de GitHub para descargar imagenes (Enter si son publicas): "
if not "!GHCR_USER!"=="" set /p "GHCR_TOKEN=Token de GitHub con permiso read:packages: "
set /p "TAILSCALE_AUTHKEY=Clave de autenticacion de Tailscale (Enter para omitir): "
set /p "HEARTBEAT_URL=URL de latido de Healthchecks.io (Enter para omitir): "
set /p "ALERT_WEBHOOK_URL=URL de webhook para alertas (Enter para omitir): "
set /p "TZ_LOCAL=Zona horaria (Enter para America/Mexico_City): "
if "!TZ_LOCAL!"=="" set "TZ_LOCAL=America/Mexico_City"

set "ARCHIVO=%TEMP%\nexus-provision-%RANDOM%.env"
> "!ARCHIVO!" echo NEXUS_DOMAIN='!NEXUS_DOMAIN!'
>> "!ARCHIVO!" echo GHCR_OWNER='!GHCR_OWNER!'
>> "!ARCHIVO!" echo CLOUDFLARE_TUNNEL_TOKEN='!CLOUDFLARE_TUNNEL_TOKEN!'
>> "!ARCHIVO!" echo SUPERADMIN_USERNAME='!SUPERADMIN_USERNAME!'
>> "!ARCHIVO!" echo GHCR_USER='!GHCR_USER!'
>> "!ARCHIVO!" echo GHCR_TOKEN='!GHCR_TOKEN!'
>> "!ARCHIVO!" echo TAILSCALE_AUTHKEY='!TAILSCALE_AUTHKEY!'
>> "!ARCHIVO!" echo HEARTBEAT_URL='!HEARTBEAT_URL!'
>> "!ARCHIVO!" echo ALERT_WEBHOOK_URL='!ALERT_WEBHOOK_URL!'
>> "!ARCHIVO!" echo TZ_LOCAL='!TZ_LOCAL!'

echo.
echo Conectando con !MP_USER!@!MP_IP! (te pedira la contrasena de ese usuario)...
echo.

ssh -o StrictHostKeyChecking=accept-new "!MP_USER!@!MP_IP!" "rm -rf ~/nexus-deploy ~/nexus-provision.env"
if errorlevel 1 goto :fallo_ssh

scp -r -o StrictHostKeyChecking=accept-new "%~dp0deploy\appliance" "!MP_USER!@!MP_IP!:nexus-deploy"
if errorlevel 1 goto :fallo_ssh

scp "!ARCHIVO!" "!MP_USER!@!MP_IP!:nexus-provision.env"
set "RC=!errorlevel!"
del /f /q "!ARCHIVO!" >nul 2>&1
if not "!RC!"=="0" goto :fallo_ssh

ssh -t "!MP_USER!@!MP_IP!" "find ~/nexus-deploy -type f -exec sed -i 's/\r$//' {} + && sudo install -m 600 -o root -g root ~/nexus-provision.env /root/nexus-provision.env && rm -f ~/nexus-provision.env && sudo bash ~/nexus-deploy/provision.sh"
if errorlevel 1 goto :fallo_provision

echo.
echo ============================================================
echo   Instalacion terminada. Abre https://!NEXUS_DOMAIN!
echo ============================================================
echo.
pause
exit /b 0

:sin_ssh
echo ERROR: este equipo no tiene ssh/scp.
echo En Windows 10/11: Configuracion ^> Aplicaciones ^> Caracteristicas opcionales ^> Cliente OpenSSH.
goto :fin_error

:faltan_datos
echo ERROR: faltan datos obligatorios. Vuelve a ejecutar y completa todos los campos requeridos.
goto :fin_error

:fallo_ssh
echo.
echo ERROR: no se pudo conectar o copiar archivos al Mini PC.
echo Revisa la IP, el usuario, la contrasena y que el Mini PC este encendido en la misma red.
if defined ARCHIVO del /f /q "!ARCHIVO!" >nul 2>&1
goto :fin_error

:fallo_provision
echo.
echo ERROR: la instalacion en el Mini PC no termino bien.
echo Entra por SSH y revisa: sudo nexus-ctl logs api   y   journalctl -t nexus
goto :fin_error

:fin_error
echo.
pause
exit /b 1
