@echo off
echo ============================================================
echo 🎮 INICIANDO PLAYERGOLD WALLET INTEGRADO
echo ============================================================
echo.

echo 🔍 Verificando permisos de administrador...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Ejecutándose como administrador
) else (
    echo ⚠️  Se requieren permisos de administrador
    echo 💡 Reinicia este script como administrador
    pause
    exit /b 1
)

echo.
echo 🧹 Limpiando procesos anteriores...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo 🔍 Liberando puertos...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18080') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18333') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo ✅ Sistema limpio
echo.
echo 🚀 Iniciando PlayerGold Wallet...
echo 💡 La wallet iniciará automáticamente:
echo    • Servicio P2P (puerto 18333)
echo    • API REST (puerto 18080)
echo    • Sincronización de blockchain
echo    • Interfaz de usuario
echo.

REM Cambiar al directorio de la wallet
cd /d "%~dp0"

REM Limpiar caché de npm
echo 🧹 Limpiando caché...
if exist node_modules\.cache rmdir /s /q node_modules\.cache
if exist build rmdir /s /q build

REM Construir la aplicación
echo 🔨 Construyendo aplicación...
call npm run build

REM Iniciar la aplicación Electron
echo 🎮 Iniciando PlayerGold Wallet...
call npm start

echo.
echo 🛑 PlayerGold Wallet cerrado
pause