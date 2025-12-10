@echo off
cd /d "%~dp0"

echo ========================================
echo COMPILACION LIMPIA - PlayerGold Wallet
echo ========================================
echo.

REM Limpiar directorios
echo [1/4] Limpiando directorios...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
echo.

REM Instalar dependencias
echo [2/4] Instalando dependencias...
call npm install
if errorlevel 1 (
    echo ERROR: Fallo en npm install
    pause
    exit /b 1
)
echo.

REM Compilar React
echo [3/4] Compilando React...
call npm run build
if errorlevel 1 (
    echo ERROR: Fallo en npm run build
    pause
    exit /b 1
)
echo.

REM Compilar Electron
echo [4/4] Compilando Electron...
call npm run electron-build
if errorlevel 1 (
    echo ERROR: Fallo en electron-build
    pause
    exit /b 1
)
echo.

echo ========================================
echo COMPILACION COMPLETADA
echo ========================================
echo.
echo Archivos generados:
dir dist\windows\*.exe 2>nul
dir dist\windows\*.zip 2>nul
echo.
pause