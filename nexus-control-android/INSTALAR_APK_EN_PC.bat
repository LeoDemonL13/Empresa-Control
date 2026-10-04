@echo off
setlocal
title Nexus Obsidian Control - Instalar en Android
cd /d "%~dp0"

echo ============================================================
echo   NEXUS OBSIDIAN CONTROL - Instalar agente en Android
echo ============================================================
echo.

where adb >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro "adb" en el PATH de este equipo.
    echo.
    echo adb viene incluido con Android Studio, normalmente en:
    echo   %%LOCALAPPDATA%%\Android\Sdk\platform-tools
    echo.
    echo Agrega esa carpeta a la variable de entorno PATH de Windows
    echo y vuelve a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

set APK=app\build\outputs\apk\debug\app-debug.apk
if not exist "%APK%" (
    set APK=app\build\outputs\apk\release\app-release.apk
)
if not exist "%APK%" (
    echo [ERROR] No se encontro ningun APK compilado.
    echo.
    echo Primero compila el proyecto desde Android Studio
    echo ^(menu Build - Build Bundle(s) / APK(s) - Build APK(s)^),
    echo o ejecuta: gradlew.bat assembleDebug
    echo.
    pause
    exit /b 1
)

echo APK encontrado: %APK%
echo.
echo Conecta el celular por USB con la "depuracion USB" activada,
echo o asegurate de que ya esta vinculado por ADB inalambrico.
echo.
pause

echo.
echo Dispositivos detectados:
adb devices
echo.

echo Instalando %APK% ...
adb install -r "%APK%"

echo.
if errorlevel 1 (
    echo [ERROR] La instalacion fallo. Revisa los mensajes anteriores.
) else (
    echo Instalacion completada. Abre "Nexus Obsidian Control" en el
    echo celular para enrolarlo con el codigo que te dio el administrador.
)
echo.
pause
