@echo off
echo ========================================
echo    PlayerGold - GamerChain Blockchain
echo    Desarrollado por Zollkron
echo ========================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python 3.9 o superior desde https://python.org
    pause
    exit /b 1
)

REM Verificar que las dependencias están instaladas
echo Verificando dependencias...
python -c "import torch, transformers, fastapi" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Faltan dependencias. Ejecutando instalación...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias
        pause
        exit /b 1
    )
)

REM Crear archivo .env si no existe
if not exist .env (
    echo Creando archivo de configuración .env...
    copy .env.example .env >nul
)

echo.
echo Dependencias verificadas correctamente
echo Iniciando PlayerGold...
echo.

REM Ejecutar el proyecto
python main.py

echo.
echo PlayerGold ha terminado de ejecutarse
pause