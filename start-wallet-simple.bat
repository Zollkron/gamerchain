@echo off
chcp 65001 >nul

:: Obtener el directorio donde se encuentra este script
set "SCRIPT_DIR=%~dp0"
:: Remover la barra final si existe
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Cambiar al directorio del script
cd /d "%SCRIPT_DIR%"

echo ========================================
echo  PlayerGold Wallet - Inicio Directo
echo  Con Genesis State Validation
echo ========================================
echo.
echo Directorio de trabajo: %CD%
echo.

:: Verificar que estamos en el directorio correcto
if not exist "wallet\package.json" (
    echo ERROR: No se encuentra wallet\package.json
    echo Directorio actual: %CD%
    echo.
    echo Ejecuta este script desde el directorio raiz del proyecto
    pause
    exit /b 1
)

:: Cambiar al directorio wallet
cd wallet

echo Iniciando PlayerGold Wallet...
echo.
echo Funcionalidades incluidas:
echo ✓ Genesis State Validation
echo ✓ Eliminacion completa de datos mock
echo ✓ WalletStateProvider para estado unificado
echo ✓ ErrorHandlingService mejorado
echo ✓ Dashboard con informacion honesta
echo.
echo La wallet se iniciara en unos segundos...
echo.

:: Iniciar la wallet
call npm start

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Error al iniciar la wallet
    echo Verifica que las dependencias esten instaladas
    echo Ejecuta: npm install
    pause
    exit /b 1
)

echo.
echo Wallet cerrada correctamente
pause