@echo off
echo ========================================
echo    PlayerGold - Instalador de Dependencias
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

echo Python encontrado:
python --version
echo.

echo Actualizando pip...
python -m pip install --upgrade pip
echo.

echo Instalando dependencias principales...
pip install cryptography ecdsa torch transformers numpy scipy fastapi uvicorn pydantic pyyaml python-dotenv structlog websockets requests click tqdm
echo.

echo Instalando dependencias de Flask...
pip install flask flask-cors flask-socketio flask-limiter flask-graphql graphene pyjwt
echo.

echo Instalando herramientas de desarrollo...
pip install pytest pytest-asyncio black flake8 mypy
echo.

echo Creando archivo de configuración...
if not exist .env (
    copy .env.example .env >nul
    echo Archivo .env creado desde .env.example
) else (
    echo Archivo .env ya existe
)

echo.
echo ========================================
echo    Instalación completada exitosamente
echo ========================================
echo.
echo Puedes ejecutar el proyecto con:
echo   - Doble clic en start.bat
echo   - O ejecutar: python main.py
echo.
pause