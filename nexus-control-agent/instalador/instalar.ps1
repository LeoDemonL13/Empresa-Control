param(
    [string]$Servidor = '',
    [string]$Codigo = '',
    [string]$Origen = '',
    [switch]$OmitirEnrolamiento
)

$ErrorActionPreference = 'Stop'

$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin) {
    Write-Host '[X] Ejecuta este instalador como Administrador.'
    exit 1
}

$nombreTarea = 'NexusObsidianControlAgente'
$carpetaPrograma = Join-Path $env:ProgramFiles 'NexusObsidianControl'
$carpetaDatos = Join-Path $env:ProgramData 'NexusObsidianControl'
$destinoExe = Join-Path $carpetaPrograma 'nexus-agente.exe'
$credenciales = Join-Path $carpetaDatos 'device.json'

if (-not $Origen) {
    $Origen = Join-Path $PSScriptRoot 'nexus-agente.exe'
}
if (-not (Test-Path $Origen)) {
    Write-Host "[X] No se encontro nexus-agente.exe en: $Origen"
    exit 1
}

$tareaPrevia = Get-ScheduledTask -TaskName $nombreTarea -ErrorAction SilentlyContinue
if ($tareaPrevia) {
    Write-Host '[..] Deteniendo la version anterior del agente.'
    Stop-ScheduledTask -TaskName $nombreTarea -ErrorAction SilentlyContinue
}
Get-Process -Name 'nexus-agente' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

New-Item -ItemType Directory -Force -Path $carpetaPrograma | Out-Null
New-Item -ItemType Directory -Force -Path $carpetaDatos | Out-Null
Copy-Item -Path $Origen -Destination $destinoExe -Force

& icacls.exe $carpetaDatos /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host '[X] No se pudieron proteger los datos del agente.'
    exit 1
}

if (-not $OmitirEnrolamiento) {
    if (-not (Test-Path $credenciales)) {
        if (-not $Servidor -or -not $Codigo) {
            Write-Host '[X] Este equipo aun no esta enrolado. Indica -Servidor y -Codigo.'
            exit 1
        }
        Write-Host '[..] Enrolando el equipo en el panel.'
        & $destinoExe --enrolar $Servidor $Codigo
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $credenciales)) {
            Write-Host '[X] No se pudo enrolar. Revisa la direccion del servidor y que el codigo no haya vencido (dura 30 minutos).'
            Write-Host "    Detalle en: $(Join-Path $carpetaDatos 'agente.log')"
            exit 1
        }
    }
    else {
        Write-Host '[OK] El equipo ya estaba enrolado; se conservan sus credenciales.'
    }
}

$accion = New-ScheduledTaskAction -Execute $destinoExe -Argument '--servicio' -WorkingDirectory $carpetaPrograma
$disparador = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$ajustes = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName $nombreTarea -Action $accion -Trigger $disparador -Principal $principal -Settings $ajustes -Force | Out-Null
Start-ScheduledTask -TaskName $nombreTarea

Start-Sleep -Seconds 3
$tarea = Get-ScheduledTask -TaskName $nombreTarea
Write-Host "[OK] Agente instalado. Estado de la tarea: $($tarea.State)"
Write-Host '[OK] Arrancara solo cada vez que se encienda el equipo.'
exit 0
