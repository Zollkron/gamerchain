@echo off
REM Test simple para verificar npm

echo ========================================
echo Test Simple de npm
echo ========================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"
echo Directorio: %CD%
echo.

echo 1. Probando node --version:
node --version
echo Código de salida node: %errorlevel%
echo.

echo 2. Probando npm --version:
npm --version
echo Código de salida npm: %errorlevel%
echo.

echo 3. Verificando ubicación de npm:
where npm
echo.

echo 4. Verificando PATH:
echo PATH: %PATH%
echo.

echo 5. Probando npm con ruta completa:
"C:\Program Files\nodejs\npm.cmd" --version 2>nul
echo Código de salida npm completo: %errorlevel%
echo.

echo ========================================
echo Test completado
echo ========================================
pause