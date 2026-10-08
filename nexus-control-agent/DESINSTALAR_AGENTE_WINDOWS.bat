@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Nexus Obsidian Control - Desinstalar agente
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalador\desinstalar.ps1"
echo.
pause
exit /b 0
