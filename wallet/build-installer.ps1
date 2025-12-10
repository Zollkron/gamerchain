# Script para compilar el instalador de PlayerGold Wallet con privilegios de administrador
# Este script debe ejecutarse como administrador

Write-Host "=== Compilando Instalador PlayerGold Wallet ===" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio del wallet
Set-Location $PSScriptRoot

# Deshabilitar la detección automática de certificados
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"

Write-Host "Limpiando caché de electron-builder..." -ForegroundColor Yellow
$cachePath = "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign"
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Caché limpiado" -ForegroundColor Green
}

Write-Host ""
Write-Host "Iniciando compilación del instalador NSIS..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar electron-builder
npx electron-builder --win nsis --publish=never

Write-Host ""
if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Compilación Exitosa ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "El instalador se encuentra en:" -ForegroundColor Cyan
    Write-Host "  dist/windows/PlayerGold Wallet Setup 1.0.0.exe" -ForegroundColor White
} else {
    Write-Host "=== Error en la Compilación ===" -ForegroundColor Red
    Write-Host "Código de salida: $LASTEXITCODE" -ForegroundColor Red
}

Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
