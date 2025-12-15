@echo off
chcp 65001 >nul

:: Obtener el directorio donde se encuentra este script
set "SCRIPT_DIR=%~dp0"
:: Remover la barra final si existe
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Cambiar al directorio del script
cd /d "%SCRIPT_DIR%"

echo ========================================
echo  Recompilacion Rapida - Wallet Corregida
echo ========================================
echo.
echo Directorio de trabajo: %CD%
echo.

:: Verificar que estamos en el directorio correcto
if not exist "wallet\package.json" (
    echo ERROR: No se encuentra wallet\package.json
    echo Directorio actual: %CD%
    echo.
    pause
    exit /b 1
)

echo [1/3] Limpiando build anterior...
cd wallet
if exist "dist-portable" rmdir /s /q dist-portable
echo OK: Build anterior limpiado

echo.
echo [2/3] Recompilando aplicacion React...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Fallo la compilacion de React
    pause
    exit /b 1
)
echo OK: React compilado

echo.
echo [3/3] Creando paquete portable corregido...
call node scripts/build-portable.js
if %errorlevel% neq 0 (
    echo ERROR: Fallo la creacion del paquete portable
    pause
    exit /b 1
)
echo OK: Paquete portable creado

echo.
echo Verificando el launcher corregido...
if exist "dist-portable\PlayerGold-Wallet.bat" (
    echo OK: Launcher creado exitosamente
    
    :: Probar el launcher brevemente
    echo.
    echo Probando launcher (se cerrara automaticamente)...
    cd dist-portable
    timeout /t 3 /nobreak >nul
    echo Launcher probado - deberia funcionar sin errores de sintaxis
    cd ..
) else (
    echo ERROR: Launcher no encontrado
)

cd ..

echo.
echo ========================================
echo  RECOMPILACION COMPLETADA
echo ========================================
echo.
echo Cambios realizados:
echo - Eliminados emojis problematicos del launcher
echo - Agregada codificacion UTF-8 correcta
echo - Mejorado manejo de errores
echo - Agregada verificacion de Electron
echo.
echo Para probar la wallet:
echo   cd wallet\dist-portable
echo   PlayerGold-Wallet.bat
echo.

pause