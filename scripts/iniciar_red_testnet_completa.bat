@echo off
REM Script completo para iniciar la red testnet PlayerGold
REM Configura firewall y inicia ambos nodos
cd /d "%~dp0"
cd ..

echo ============================================================
echo 🚀 INICIANDO RED TESTNET PLAYERGOLD COMPLETA
echo ============================================================
echo.

REM Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Ejecutándose como Administrador
) else (
    echo ❌ ERROR: Este script debe ejecutarse como Administrador
    echo.
    echo 💡 Clic derecho en el archivo y seleccionar "Ejecutar como administrador"
    pause
    exit /b 1
)

echo.
echo 🔧 Paso 1: Configurando firewall...
call scripts\configurar_firewall_testnet.bat

echo.
echo 🔍 Paso 2: Ejecutando diagnóstico de red...
python scripts\diagnostico_red_testnet.py

echo.
echo 🖥️  Paso 3: Iniciando nodos testnet...
echo.
echo ⚠️  IMPORTANTE: 
echo    - Este script iniciará el Nodo 1 en esta máquina
echo    - Debes ejecutar el Nodo 2 manualmente en el portátil
echo    - O usar el script equivalente en el portátil
echo.

set /p continuar="¿Continuar con el inicio del Nodo 1? (S/N): "
if /i "%continuar%" neq "S" (
    echo Operación cancelada por el usuario
    pause
    exit /b 0
)

echo.
echo 🚀 Iniciando Nodo 1 (Principal)...
echo.
echo 📋 Comandos para el portátil:
echo    1. Copiar todo el proyecto gamerchain al portátil
echo    2. Ejecutar: scripts\start_node2_testnet.bat
echo    3. O ejecutar: scripts\iniciar_nodo2_portatil.bat
echo.

REM Iniciar nodo 1 en una nueva ventana
start "PlayerGold Nodo 1" cmd /k "scripts\start_node1_testnet.bat"

echo.
echo ✅ Nodo 1 iniciado en ventana separada
echo.
echo 📊 Para monitorear la red:
echo    python scripts\diagnostico_red_testnet.py
echo.
echo 🎮 Para iniciar wallets:
echo    cd wallet
echo    .\clear-cache-and-start.bat
echo.

pause