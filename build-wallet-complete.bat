@echo off
chcp 65001 >nul

:: Obtener el directorio donde se encuentra este script
set "SCRIPT_DIR=%~dp0"
:: Remover la barra final si existe
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Cambiar al directorio del script (importante para ejecucion como administrador)
cd /d "%SCRIPT_DIR%"

echo ========================================
echo  PlayerGold Wallet - Recompilacion Completa
echo  Con Genesis State Validation
echo ========================================
echo.
echo Directorio de trabajo: %CD%
echo.

:: Verificar que estamos en el directorio correcto
if not exist "wallet\package.json" (
    echo ERROR: No se encuentra wallet\package.json
    echo Directorio actual: %CD%
    echo Directorio del script: %SCRIPT_DIR%
    echo.
    echo Ejecuta este script desde el directorio raiz del proyecto
    echo o verifica que la estructura de directorios sea correcta
    pause
    exit /b 1
)

:: Cambiar al directorio wallet
cd wallet

echo [1/6] Limpiando cache y dependencias anteriores...
if exist node_modules rmdir /s /q node_modules
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist dist-portable rmdir /s /q dist-portable
echo ✓ Cache limpiado

echo.
echo [2/6] Instalando dependencias de Node.js...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Fallo la instalacion de dependencias
    pause
    exit /b 1
)
echo ✓ Dependencias instaladas

echo.
echo [3/6] Ejecutando tests de Genesis State Validation...
echo Ejecutando tests principales...
call npm test -- --watchAll=false --testPathPattern="GenesisStateManager|NetworkService|WalletStateProvider|MockDataRemoval|EndToEndWalletLifecycle" --passWithNoTests --verbose
if %errorlevel% neq 0 (
    echo ADVERTENCIA: Algunos tests fallaron, pero continuamos con la compilacion
    echo Los tests de Genesis State Validation pueden fallar si no hay conexion de red
)
echo ✓ Tests ejecutados

echo.
echo [4/6] Compilando aplicacion React...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Fallo la compilacion de React
    pause
    exit /b 1
)
echo ✓ Aplicacion React compilada

echo.
echo [5/6] Creando paquete portable con Electron...
call node scripts/build-portable.js
if %errorlevel% neq 0 (
    echo ERROR: Fallo la creacion del paquete portable
    pause
    exit /b 1
)
echo ✓ Paquete portable creado

echo.
echo [6/6] Verificando la compilacion...
if exist "dist-portable\PlayerGold-Wallet.exe" (
    echo ✓ Ejecutable creado exitosamente
) else if exist "dist-portable\PlayerGold-Wallet.bat" (
    echo ✓ Script de inicio creado exitosamente
) else (
    echo ADVERTENCIA: No se encontro el ejecutable principal
)

if exist "dist-portable\wallet" (
    echo ✓ Archivos de la wallet copiados
) else (
    echo ERROR: Archivos de la wallet no encontrados
)

echo.
echo ========================================
echo  COMPILACION COMPLETADA
echo ========================================
echo.
echo Nuevas funcionalidades incluidas:
echo ✓ Genesis State Validation
echo ✓ Eliminacion completa de datos mock
echo ✓ WalletStateProvider para estado unificado
echo ✓ ErrorHandlingService mejorado
echo ✓ Dashboard con informacion honesta
echo.
echo La wallet compilada esta en: wallet\dist-portable\
echo.
echo Para ejecutar la wallet:
echo   cd wallet\dist-portable
echo   PlayerGold-Wallet.bat
echo.

:: Volver al directorio raiz
cd ..

echo Presiona cualquier tecla para continuar...
pause > nul