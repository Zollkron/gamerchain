@echo off
title PlayerGold Wallet - Hecho por gamers para gamers
echo.
echo ===============================================
echo    PlayerGold Wallet - Starting...
echo    Hecho por gamers para gamers
echo ===============================================
echo.

REM Automatic Environment Detection and Configuration
echo 🔍 Detectando entorno del sistema...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Por favor instala Python 3.8 o superior.
    echo    Descarga desde: https://www.python.org/downloads/
    echo    ⚠️  IMPORTANTE: Marca "Add Python to PATH" durante la instalacion.
    echo.
    echo 💡 Despues de instalar Python, ejecuta este archivo de nuevo.
    pause
    exit /b 1
)

REM Check if Node.js is installed  
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js no encontrado. Por favor instala Node.js.
    echo    Descarga desde: https://nodejs.org/
    echo    💡 Recomendamos la version LTS (Long Term Support).
    echo.
    echo 💡 Despues de instalar Node.js, ejecuta este archivo de nuevo.
    pause
    exit /b 1
)

echo ✅ Requisitos del sistema verificados correctamente.
echo.

REM Automatic Environment Configuration
echo ⚙️ Configurando entorno automáticamente...

REM Install Python dependencies if needed
if not exist "backend\venv" (
    echo 🐍 Configurando entorno Python por primera vez...
    echo    Esto puede tomar unos minutos...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Error instalando dependencias Python.
        echo    Verifica tu conexion a Internet e intenta de nuevo.
        pause
        exit /b 1
    )
    cd ..
    echo ✅ Entorno Python configurado correctamente.
)

REM Create comprehensive data directory structure
echo 📁 Creando estructura de directorios...
if not exist "data" mkdir data
if not exist "data\wallets" mkdir data\wallets
if not exist "data\blockchain" mkdir data\blockchain
if not exist "data\logs" mkdir data\logs
if not exist "data\models" mkdir data\models
if not exist "data\temp" mkdir data\temp

REM Pioneer Mode Initialization for New Installations
if not exist "data\bootstrap-state.json" (
    echo 🚀 Primera instalación detectada - Inicializando modo pionero...
    echo {"mode":"pioneer","initialized":true,"timestamp":"%date% %time%","version":"1.0.0","portable":true} > data\bootstrap-state.json
    echo ✅ Modo pionero inicializado. ¡Listo para crear la red!
    echo.
    echo 🎮 ¿Qué significa esto?
    echo    - Eres un usuario pionero de PlayerGold
    echo    - Tu wallet buscará automáticamente otros usuarios
    echo    - Cuando encuentre otros pioneros, crearán la red juntos
    echo    - ¡No necesitas hacer nada técnico!
    echo.
)

REM Set environment variables for portable mode
set PLAYERGOLD_PORTABLE=true
set PLAYERGOLD_DATA_DIR=%cd%\data
set PLAYERGOLD_BOOTSTRAP_MODE=auto
set NODE_ENV=production

REM Final system check
echo 🔧 Verificación final del sistema...
python -c "import sys; print(f'Python {sys.version}')" 2>nul
node --version 2>nul
echo.

REM Start the wallet with enhanced portable mode support
echo 🚀 Iniciando PlayerGold Wallet en modo portable...
echo    Modo: Pionero automático
echo    Directorio de datos: %cd%\data
echo.
cd wallet
electron . --portable --pioneer-mode --no-sandbox

if errorlevel 1 (
    echo.
    echo ❌ Error al iniciar la wallet.
    echo 💡 Posibles soluciones:
    echo    1. Reinicia tu computadora e intenta de nuevo
    echo    2. Ejecuta como administrador
    echo    3. Verifica que no hay antivirus bloqueando la aplicacion
    echo.
)

pause
