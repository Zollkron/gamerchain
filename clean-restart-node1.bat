@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo Limpiar y Reiniciar Nodo 1 Correctamente
echo ========================================
echo.
echo Directorio de trabajo: %CD%
echo.

echo 🧹 Limpiando datos falsos de blockchain...

REM Limpiar datos de testnet que puedan estar causando el problema
if exist "data\testnet" (
    echo 📁 Eliminando datos de testnet falsos...
    rmdir /s /q "data\testnet" 2>nul
    echo ✅ Datos de testnet eliminados
)

REM Limpiar logs que puedan contener estado falso
if exist "logs" (
    echo 📁 Limpiando logs...
    del /q "logs\*.log" 2>nul
    echo ✅ Logs limpiados
)

REM Limpiar cache de wallet
if exist "wallet\node_modules\.cache" (
    echo 📁 Limpiando cache de wallet...
    rmdir /s /q "wallet\node_modules\.cache" 2>nul
    echo ✅ Cache limpiado
)

echo.
echo 🔧 Correcciones aplicadas:
echo   ✓ GenesisStateManager corregido - ya no acepta datos falsos
echo   ✓ NetworkService getMiningChallenge arreglado
echo   ✓ Python IndentationError corregido
echo   ✓ Datos falsos de blockchain eliminados
echo.

echo 🚀 Iniciando Nodo Génesis 1 limpio...
echo.

echo 📋 Estado esperado:
echo   ⏳ "No genesis block found - this is expected for bootstrap mode"
echo   ✅ Network Coordinator conectado
echo   ✅ P2P Network activo en puerto 18080
echo   ✅ Esperando Nodo 2 para crear génesis real
echo.

cd wallet
npm start

echo.
echo ========================================
echo Nodo 1 reiniciado limpiamente
echo ========================================
pause