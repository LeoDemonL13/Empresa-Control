param(
    [switch]$Finalizar,
    [string]$Usuario,
    [string]$Clave,
    [string]$Nombre
)

$ErrorActionPreference = 'Stop'

$raiz = Split-Path -Parent $PSScriptRoot
$api = Join-Path $raiz 'nexus-control-api'
$rutaEnv = Join-Path $api '.env'
$rutaEjemplo = Join-Path $api '.env.example'
$codificacion = New-Object System.Text.UTF8Encoding($false)

function Nuevos-Bytes([int]$cantidad) {
    $bytes = New-Object byte[] $cantidad
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    return ,$bytes
}

function Nueva-ClaveUrlSegura {
    $bytes = Nuevos-Bytes 32
    return [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_')
}

function Nueva-ClaveHex([int]$cantidad) {
    $bytes = Nuevos-Bytes $cantidad
    return (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Aplicar-Valores([string[]]$lineas, [hashtable]$valores) {
    $vistos = @{}
    $salida = New-Object System.Collections.Generic.List[string]
    foreach ($linea in $lineas) {
        $m = [regex]::Match($linea, '^\s*([A-Za-z0-9_]+)=')
        if ($m.Success -and $valores.ContainsKey($m.Groups[1].Value)) {
            $nombre = $m.Groups[1].Value
            $salida.Add("$nombre=$($valores[$nombre])")
            $vistos[$nombre] = $true
        } else {
            $salida.Add($linea)
        }
    }
    foreach ($nombre in $valores.Keys) {
        if (-not $vistos.ContainsKey($nombre)) {
            $salida.Add("$nombre=$($valores[$nombre])")
        }
    }
    return $salida.ToArray()
}

function Guardar-Env([string[]]$lineas) {
    $texto = ($lineas -join "`n") + "`n"
    [System.IO.File]::WriteAllText($rutaEnv, $texto, $codificacion)
}

function Leer-Texto([string]$mensaje) {
    return (Read-Host $mensaje).Trim()
}

function Leer-ClaveOculta([string]$mensaje) {
    $segura = Read-Host $mensaje -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Motivo-ClaveInvalida([string]$clave) {
    if ($clave.Length -lt 12) { return 'Debe tener al menos 12 caracteres.' }
    if ($clave -cnotmatch '[A-Z]') { return 'Debe incluir una mayuscula.' }
    if ($clave -cnotmatch '[a-z]') { return 'Debe incluir una minuscula.' }
    if ($clave -notmatch '[0-9]') { return 'Debe incluir un numero.' }
    if ($clave -notmatch '[^A-Za-z0-9]') { return 'Debe incluir un simbolo.' }
    if ($clave.Contains("'") -or $clave.Contains('"') -or $clave -match '[\r\n]') {
        return 'No puede incluir comillas ni saltos de linea.'
    }
    return $null
}

function Limpiar-Texto([string]$texto) {
    return ($texto -replace "['`"\r\n]", '').Trim()
}

if ($Finalizar) {
    if (-not (Test-Path $rutaEnv)) { exit 0 }
    $lineas = [System.IO.File]::ReadAllLines($rutaEnv)
    $tieneClave = $false
    foreach ($linea in $lineas) {
        if ($linea -match "^\s*SUPERADMIN_PASSWORD=(.+)$" -and $Matches[1].Trim().Trim("'") -ne '') {
            $tieneClave = $true
        }
    }
    if (-not $tieneClave) { exit 0 }
    $nuevas = Aplicar-Valores $lineas @{
        'SUPERADMIN_PASSWORD' = ''
        'CREAR_SUPER_ADMIN' = 'false'
        'SUPERADMIN_FORZAR_PASSWORD' = 'false'
    }
    Guardar-Env $nuevas
    Write-Host 'La clave del super administrador se borro del archivo .env.'
    exit 0
}

if (Test-Path $rutaEnv) {
    Write-Host 'El archivo .env ya existe. No se modifica.'
    exit 0
}

if (-not (Test-Path $rutaEjemplo)) {
    Write-Host 'No se encontro nexus-control-api\.env.example.'
    exit 1
}

Write-Host ''
Write-Host 'Primera configuracion de Nexus Obsidian Control'
Write-Host 'Se generan solas las claves de seguridad. Solo falta crear al super administrador.'
Write-Host ''

if (-not $Usuario) {
    do {
        $Usuario = Limpiar-Texto (Leer-Texto 'Usuario del super administrador (correo o nombre)')
    } while (-not $Usuario)
}
$Usuario = Limpiar-Texto $Usuario

if (-not $Nombre -and -not $PSBoundParameters.ContainsKey('Clave')) {
    $Nombre = Leer-Texto 'Nombre completo (opcional, Enter para omitir)'
}
$Nombre = Limpiar-Texto $Nombre

if ($Clave) {
    $motivo = Motivo-ClaveInvalida $Clave
    if ($motivo) {
        Write-Host $motivo
        exit 1
    }
} else {
    Write-Host ''
    Write-Host 'La clave lleva al menos 12 caracteres, con mayuscula, minuscula, numero y simbolo.'
    while ($true) {
        $primera = Leer-ClaveOculta 'Clave del super administrador'
        $motivo = Motivo-ClaveInvalida $primera
        if ($motivo) {
            Write-Host $motivo
            continue
        }
        $segunda = Leer-ClaveOculta 'Repite la clave'
        if ($primera -cne $segunda) {
            Write-Host 'Las claves no coinciden.'
            continue
        }
        $Clave = $primera
        break
    }
}

$base = [System.IO.File]::ReadAllLines($rutaEjemplo)
$valores = [ordered]@{
    'SECRET_KEY' = (Nueva-ClaveUrlSegura)
    'TOTP_ENCRYPTION_KEY' = (Nueva-ClaveUrlSegura)
    'SOCIAL_TOKEN_ENCRYPTION_KEY' = (Nueva-ClaveUrlSegura)
    'POSTGRES_PASSWORD' = (Nueva-ClaveHex 24)
    'CREAR_SUPER_ADMIN' = 'true'
    'SUPERADMIN_USERNAME' = "'$Usuario'"
    'SUPERADMIN_PASSWORD' = "'$Clave'"
    'SUPERADMIN_FULL_NAME' = "'$Nombre'"
    'SUPERADMIN_FORZAR_PASSWORD' = 'false'
}
Guardar-Env (Aplicar-Valores $base $valores)

Write-Host ''
Write-Host 'Archivo .env creado.'
