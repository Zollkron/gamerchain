@echo off
REM PlayerGold Wallet - Build con Debug Completo
REM Versión que muestra EXACTAMENTE qué está pasando en cada paso

echo ========================================
echo PlayerGold Wallet - Build DEBUG
echo ========================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"
echo DEBUG: Directorio actual: %CD%
echo.

REM Verificar estructura básica
echo DEBUG: Verificando estructura del proyecto...
if not exist "wallet\package.json" (
    echo ERROR: No se encuentra wallet\package.json
    echo Directorio actual: %CD%
    dir
    pause
    exit /b 1
)
echo DEBUG: wallet\package.json encontrado ✓
echo.

REM Verificar Node.js
echo DEBUG: Verificando Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js no funciona
    pause
    exit /b 1
)
echo DEBUG: Node.js funciona ✓
echo.

REM Verificar npm
echo DEBUG: Verificando npm...
npm --version
if errorlevel 1 (
    echo ERROR: npm no funciona
    pause
    exit /b 1
)
echo DEBUG: npm funciona ✓
echo.

REM Cambiar a directorio wallet
echo DEBUG: Cambiando a directorio wallet...
cd wallet
echo DEBUG: Nuevo directorio: %CD%
echo.

REM Verificar package.json en wallet
echo DEBUG: Verificando package.json en wallet...
if not exist "package.json" (
    echo ERROR: No hay package.json en directorio wallet
    echo Directorio actual: %CD%
    dir
    pause
    exit /b 1
)
echo DEBUG: package.json en wallet encontrado ✓
echo.

REM Limpiar builds anteriores
echo DEBUG: Limpiando builds anteriores...
if exist "build" (
    echo DEBUG: Eliminando build/
    rmdir /s /q "build"
)
if exist "dist" (
    echo DEBUG: Eliminando dist/
    rmdir /s /q "dist"
)
echo DEBUG: Limpieza completada ✓
echo.

REM Instalar dependencias
echo DEBUG: Instalando dependencias npm...
echo DEBUG: Esto puede tomar varios minutos, por favor espera...
call npm install
if errorlevel 1 (
    echo ERROR: npm install falló
    pause
    exit /b 1
)
echo DEBUG: npm install completado ✓
echo.

REM Build React
echo DEBUG: Construyendo aplicación React...
echo DEBUG: Esto puede tomar varios minutos, por favor espera...
call npm run build
if errorlevel 1 (
    echo ERROR: npm run build falló
    pause
    exit /b 1
)
echo DEBUG: React build completado ✓
echo.

REM Build Electron
echo DEBUG: Empaquetando con Electron...
echo DEBUG: Esto puede tomar varios minutos, por favor espera...
call npm run electron-build
if errorlevel 1 (
    echo ERROR: npm run electron-build falló
    pause
    exit /b 1
)
echo DEBUG: Electron build completado ✓
echo.

REM Volver al directorio raíz
cd ..
echo DEBUG: Volviendo al directorio raíz: %CD%
echo.

REM Verificar archivos generados
echo DEBUG: Verificando archivos generados...
if exist "wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe" (
    echo DEBUG: ✓ Ejecutable portable encontrado
) else (
    echo DEBUG: ❌ Ejecutable portable NO encontrado
)

if exist "wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe" (
    echo DEBUG: ✓ Instalador encontrado
) else (
    echo DEBUG: ❌ Instalador NO encontrado
)
echo.

echo ========================================
echo BUILD COMPLETADO
echo ========================================
echo.
echo Archivos generados:
if exist "wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe" (
    echo ✓ Ejecutable: wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe
)
if exist "wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe" (
    echo ✓ Instalador: wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe
)
echo.
pause