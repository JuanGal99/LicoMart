# ============================================================
#  LicoMart - Arranque completo con un solo comando
#  Uso:  .\iniciar.ps1          (datos existentes)
#        .\iniciar.ps1 -Seed    (borra y recarga datos demo)
# ============================================================
param([switch]$Seed)

$ErrorActionPreference = "Stop"

$seedFlag = "false"
if ($Seed) {
    $seedFlag = "true"
    Write-Host ""
    Write-Host "  Se borraran TODOS los datos y se cargaran datos de demostracion." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Construyendo e iniciando LicoMart..." -ForegroundColor Cyan
Write-Host ""

$env:SEED_ON_START = $seedFlag
docker compose up --build -d
$env:SEED_ON_START = $null

Write-Host ""
Write-Host "Esperando a que los servicios esten listos..." -ForegroundColor Cyan

$retries = 40
while ($retries -gt 0) {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 3
        break
    } catch {
        $retries--
        if ($retries -le 0) {
            Write-Host "Timeout esperando los servicios. Revisa: docker compose logs" -ForegroundColor Red
            exit 1
        }
        Start-Sleep -Seconds 3
    }
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  LicoMart esta corriendo" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  URL:  http://localhost:5173" -ForegroundColor White
Write-Host ""

if ($Seed) {
    Write-Host "  CREDENCIALES:" -ForegroundColor Yellow
    Write-Host "  ----------------------------------------"
    Write-Host "  Rol: admin       Usuario: admin       Clave: Admin2026!"
    Write-Host "  Rol: usuario     Usuario: usuario     Clave: Usuario2026!"
    Write-Host "  ----------------------------------------"
} else {
    Write-Host "  Para cargar datos demo: .\iniciar.ps1 -Seed" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Logs:   docker compose logs -f"
Write-Host "  Parar:  docker compose down"
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
