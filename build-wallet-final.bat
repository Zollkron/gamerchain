@echo off
setlocal enabledelayedexpansion

echo ========================================
echo PlayerGold Wallet - Build FINAL
echo ========================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"
echo Directorio: %CD%
echo.

REM Verificar estructura
if not exist "wallet\package.json" (
    echo ERROR: No se encuentra wallet\package.json
    pause
    exit /b 1
)
echo ✓ Estructura del proyecto verificada
echo.

REM Verificar herramientas (sin usar npm --version que causa problemas)
echo Verificando herramientas...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no encontrado
    pause
    exit /b 1
)
echo ✓ Node.js disponible

REM Para npm, vamos a verificar de otra manera
where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm no encontrado en PATH
    pause
    exit /b 1
)
echo ✓ npm disponible
echo.

REM Cambiar a directorio wallet
echo Cambiando a directorio wallet...
cd wallet
if not exist "package.json" (
    echo ERROR: package.json no encontrado en wallet
    pause
    exit /b 1
)
echo ✓ En directorio wallet
echo.

REM Limpiar builds anteriores
echo Limpiando builds anteriores...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
echo ✓ Limpieza completada
echo.

REM Instalar dependencias
echo ========================================
echo INSTALANDO DEPENDENCIAS
echo ========================================
echo Esto puede tomar varios minutos...
echo.
call npm install
if errorlevel 1 (
    echo.
    echo ERROR: npm install falló
    echo Intentando con --force...
    call npm install --force
    if errorlevel 1 (
        echo ERROR: npm install --force también falló
        pause
        exit /b 1
    )
)
echo.
echo ✓ Dependencias instaladas
echo.

REM Build React
echo ========================================
echo CONSTRUYENDO REACT
echo ========================================
echo Esto puede tomar varios minutos...
echo.
call npm run build
if errorlevel 1 (
    echo ERROR: npm run build falló
    pause
    exit /b 1
)
echo.
echo ✓ React build completado
echo.

REM Build Electron
echo ========================================
echo EMPAQUETANDO ELECTRON
echo ========================================
echo Esto puede tomar varios minutos...
echo.
call npm run electron-build
if errorlevel 1 (
    echo ERROR: npm run electron-build falló
    pause
    exit /b 1
)
echo.
echo ✓ Electron build completado
echo.

REM Volver al directorio raíz
cd ..

REM Verificar resultados
echo ========================================
echo VERIFICANDO RESULTADOS
echo ========================================
echo.

set PORTABLE_EXE=wallet\dist\windows\win-unpacked\PlayerGold Wallet.exe
set INSTALLER_EXE=wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe

if exist "%PORTABLE_EXE%" (
    echo ✓ Ejecutable portable: %PORTABLE_EXE%
    set PORTABLE_OK=1
) else (
    echo ❌ Ejecutable portable NO encontrado
    set PORTABLE_OK=0
)

if exist "%INSTALLER_EXE%" (
    echo ✓ Instalador: %INSTALLER_EXE%
    set INSTALLER_OK=1
) else (
    echo ❌ Instalador NO encontrado
    set INSTALLER_OK=0
)

echo.
if %PORTABLE_OK%==1 (
    echo ========================================
    echo ✅ BUILD EXITOSO
    echo ========================================
    echo.
    echo Archivos generados:
    echo • Ejecutable portable: %PORTABLE_EXE%
    if %INSTALLER_OK%==1 echo • Instalador: %INSTALLER_EXE%
    echo.
    echo Para probar: ejecuta el archivo portable
) else (
    echo ========================================
    echo ❌ BUILD FALLÓ
    echo ========================================
    echo No se generaron los archivos esperados
)

echo.
pause