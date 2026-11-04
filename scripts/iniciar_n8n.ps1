# Arranca n8n en este PC sin Docker (con Node), en el puerto 5679 y con su propia carpeta.
# Uso (desde la carpeta del repo):   powershell -ExecutionPolicy Bypass -File scripts\iniciar_n8n.ps1
# Para pararlo: Ctrl+C en esa ventana.

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$puerto = 5679
$version = "2.44.7"   # versión de n8n probada con este flujo (Node 24)
$puertoBroker = 5699  # n8n abre un 2.º puerto interno (por defecto 5679): se mueve para que no choque

# ¿Ya hay algo usando el puerto?
foreach ($p in @($puerto, $puertoBroker)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue) {
        Write-Host "El puerto $p ya está en uso. Cierra lo que lo usa o cambia el puerto en este script." -ForegroundColor Yellow
        exit 1
    }
}

$env:N8N_PORT = "$puerto"
$env:N8N_RUNNERS_BROKER_PORT = "$puertoBroker"
$env:N8N_USER_FOLDER = Join-Path $raiz ".n8n_local"          # datos de n8n de este proyecto (no se suben)
$env:N8N_RESTRICT_FILE_ACCESS_TO = (Join-Path $raiz "datos") + ";" + (Join-Path $raiz "registro")
$env:N8N_DIAGNOSTICS_ENABLED = "false"
$env:N8N_SECURE_COOKIE = "false"
$env:GENERIC_TIMEZONE = "America/Bogota"

Set-Location $raiz
py -3.12 scripts\preparar_registro.py
Write-Host "n8n en http://localhost:$puerto  (carpeta de datos: .n8n_local)" -ForegroundColor Cyan
npx --yes "n8n@$version" start
