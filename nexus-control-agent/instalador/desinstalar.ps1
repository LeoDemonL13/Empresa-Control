param(
    [switch]$ConservarDatos
)

$ErrorActionPreference = 'Stop'

$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin) {
    Write-Host '[X] Ejecuta este desinstalador como Administrador.'
    exit 1
}

$nombreTarea = 'NexusObsidianControlAgente'
$carpetaPrograma = Join-Path $env:ProgramFiles 'NexusObsidianControl'
$carpetaDatos = Join-Path $env:ProgramData 'NexusObsidianControl'

if (Get-ScheduledTask -TaskName $nombreTarea -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $nombreTarea -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $nombreTarea -Confirm:$false
}
Get-Process -Name 'nexus-agente' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

if (Test-Path $carpetaPrograma) {
    Remove-Item -Recurse -Force $carpetaPrograma
}
if ((-not $ConservarDatos) -and (Test-Path $carpetaDatos)) {
    Remove-Item -Recurse -Force $carpetaDatos
}

Write-Host '[OK] Agente desinstalado. Si el equipo ya no se va a usar, eliminalo tambien desde el panel (Equipos).'
exit 0
