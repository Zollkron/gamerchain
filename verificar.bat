@echo off
echo ========================================
echo    PlayerGold - Verificación del Sistema
echo ========================================
echo.

echo Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado
    pause
    exit /b 1
)
echo ✅ Python instalado correctamente
echo.

echo Verificando pip...
pip --version
if errorlevel 1 (
    echo ❌ ERROR: pip no está disponible
    pause
    exit /b 1
)
echo ✅ pip disponible
echo.

echo Verificando dependencias principales...
python -c "import torch; print('✅ PyTorch:', torch.__version__)"
if errorlevel 1 (
    echo ❌ ERROR: PyTorch no está instalado
    goto :install_deps
)

python -c "import transformers; print('✅ Transformers:', transformers.__version__)"
if errorlevel 1 (
    echo ❌ ERROR: Transformers no está instalado
    goto :install_deps
)

python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
if errorlevel 1 (
    echo ❌ ERROR: FastAPI no está instalado
    goto :install_deps
)

echo.
echo ✅ Todas las dependencias están instaladas correctamente
echo.

echo Verificando configuración...
if exist .env (
    echo ✅ Archivo .env encontrado
) else (
    echo ⚠️  Archivo .env no encontrado, creando desde .env.example...
    copy .env.example .env >nul
    echo ✅ Archivo .env creado
)

echo.
echo ========================================
echo    ✅ SISTEMA LISTO PARA USAR
echo ========================================
echo.
echo Puedes ejecutar PlayerGold con:
echo   - Doble clic en start.bat
echo   - O ejecutar: python main.py
echo.
pause
exit /b 0

:install_deps
echo.
echo ⚠️  Faltan dependencias. ¿Quieres instalarlas ahora? (S/N)
set /p choice=
if /i "%choice%"=="S" (
    echo Ejecutando instalación...
    call install.bat
) else (
    echo Instalación cancelada. Ejecuta install.bat cuando estés listo.
)
pause