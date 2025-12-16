@echo off
REM PlayerGold Wallet - Limpieza de Datos Persistentes
REM Este script elimina todos los datos de wallet almacenados en el sistema

echo ========================================
echo PlayerGold Wallet - Limpieza de Datos
echo ========================================
echo.
echo ⚠️  ADVERTENCIA: Este script eliminará TODOS los datos de wallet
echo    incluyendo wallets creadas, configuraciones y datos persistentes.
echo.
echo 💡 Esto es útil para:
echo    • Probar la wallet en un estado completamente limpio
echo    • Resolver problemas de datos corruptos
echo    • Simular una instalación completamente nueva
echo.

set /p CONFIRM="¿Estás seguro de que quieres continuar? (S/N): "
if /i not "%CONFIRM%"=="S" (
    echo Operación cancelada.
    pause
    exit /b 0
)

echo.
echo 🧹 Iniciando limpieza de datos...
echo.

REM Limpiar datos de electron-store (ubicaciones comunes en Windows)
echo • Limpiando datos de electron-store...

REM AppData\Roaming\playergold-wallet (nombre de la app)
if exist "%APPDATA%\playergold-wallet" (
    echo   - Eliminando %APPDATA%\playergold-wallet
    rmdir /s /q "%APPDATA%\playergold-wallet" 2>nul
)

REM AppData\Roaming\PlayerGold Wallet (nombre con espacios)
if exist "%APPDATA%\PlayerGold Wallet" (
    echo   - Eliminando "%APPDATA%\PlayerGold Wallet"
    rmdir /s /q "%APPDATA%\PlayerGold Wallet" 2>nul
)

REM Archivos específicos de electron-store
if exist "%APPDATA%\playergold-wallets.json" (
    echo   - Eliminando %APPDATA%\playergold-wallets.json
    del "%APPDATA%\playergold-wallets.json" 2>nul
)

if exist "%APPDATA%\playergold-wallets.json.tmp" (
    echo   - Eliminando %APPDATA%\playergold-wallets.json.tmp
    del "%APPDATA%\playergold-wallets.json.tmp" 2>nul
)

REM Limpiar localStorage del navegador (si se usa en desarrollo)
echo • Limpiando datos de localStorage...

REM Limpiar datos temporales de la aplicación
echo • Limpiando datos temporales...
if exist "%TEMP%\playergold*" (
    echo   - Eliminando archivos temporales de PlayerGold
    del /q "%TEMP%\playergold*" 2>nul
)

REM Limpiar datos en el directorio de la aplicación
echo • Limpiando datos locales de la aplicación...
if exist "wallet\data" (
    echo   - Eliminando wallet\data
    rmdir /s /q "wallet\data" 2>nul
)

if exist "wallet\temp" (
    echo   - Eliminando wallet\temp
    rmdir /s /q "wallet\temp" 2>nul
)

if exist "wallet\logs" (
    echo   - Eliminando wallet\logs
    rmdir /s /q "wallet\logs" 2>nul
)

REM Limpiar archivos de configuración local
if exist "wallet\.playergold" (
    echo   - Eliminando wallet\.playergold
    rmdir /s /q "wallet\.playergold" 2>nul
)

REM Limpiar builds anteriores
echo • Limpiando builds anteriores...
if exist "wallet\build" (
    echo   - Eliminando wallet\build
    rmdir /s /q "wallet\build" 2>nul
)

if exist "wallet\dist" (
    echo   - Eliminando wallet\dist
    rmdir /s /q "wallet\dist" 2>nul
)

echo.
echo ========================================
echo ✅ LIMPIEZA COMPLETADA
echo ========================================
echo.
echo 📋 Datos eliminados:
echo    • Configuraciones de electron-store
echo    • Datos de wallets almacenadas
echo    • Archivos temporales
echo    • Builds anteriores
echo    • Logs y datos de desarrollo
echo.
echo 💡 PRÓXIMOS PASOS:
echo.
echo 1. PARA CONSTRUIR WALLET LIMPIA:
echo    • Ejecutar: build-wallet-final.bat
echo    • La wallet se iniciará completamente limpia
echo    • Mostrará la pantalla de crear/importar wallet
echo.
echo 2. PARA VERIFICAR LIMPIEZA:
echo    • La wallet no debe tener wallets precargadas
echo    • Debe mostrar la pantalla de configuración inicial
echo    • No debe tener datos de sesiones anteriores
echo.
echo ✅ ¡Sistema listo para una instalación completamente limpia!
echo.
pause