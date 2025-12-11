@echo off
REM Script para iniciar red testnet completa con verificación de conexión
setlocal enabledelayedexpansion

cd /d "%~dp0"
cd ..

echo ============================================================
echo 🚀 INICIANDO RED TESTNET PLAYERGOLD COMPLETA
echo ============================================================
echo.

REM Verificar si estamos ejecutando como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Este script requiere permisos de Administrador
    echo 💡 Haz clic derecho y selecciona "Ejecutar como administrador"
    pause
    exit /b 1
)

echo 🔧 Configurando firewall...
call scripts\configurar_firewall_testnet.bat

echo.
echo 🔍 Liberando puerto 18333 si está ocupado...
call scripts\liberar_puerto_18333.bat

echo.
echo 🔍 Diagnosticando configuración de red...
python scripts\diagnosticar_conexion_nodos.py

echo.
echo ============================================================
echo 🎯 INICIANDO NODOS TESTNET
echo ============================================================

REM Cargar configuración desde .env.local
if not exist ".env.local" (
    echo ❌ Archivo .env.local no encontrado
    echo.
    echo 💡 Crea el archivo .env.local con tu configuración:
    echo    NODE1_IP=TU_IP_NODO_1
    echo    NODE2_IP=TU_IP_NODO_2
    echo    CURRENT_NODE=1_o_2
    echo.
    echo 📋 Ejemplo:
    echo    NODE1_IP=192.168.1.100
    echo    NODE2_IP=192.168.1.101
    echo    CURRENT_NODE=1
    echo.
    pause
    exit /b 1
)

REM Leer variables de entorno desde .env.local
for /f "usebackq tokens=1,2 delims==" %%a in (".env.local") do (
    if "%%a"=="NODE1_IP" set "NODE1_IP=%%b"
    if "%%a"=="NODE2_IP" set "NODE2_IP=%%b"
    if "%%a"=="CURRENT_NODE" set "CURRENT_NODE=%%b"
)

REM Verificar que las variables estén configuradas
if not defined NODE1_IP (
    echo ❌ Variable NODE1_IP no definida en .env.local
    pause
    exit /b 1
)
if not defined NODE2_IP (
    echo ❌ Variable NODE2_IP no definida en .env.local
    pause
    exit /b 1
)
if not defined CURRENT_NODE (
    echo ❌ Variable CURRENT_NODE no definida en .env.local
    pause
    exit /b 1
)

REM Determinar configuración del nodo basado en CURRENT_NODE
if "%CURRENT_NODE%"=="1" (
    set "node_type=1"
    set "node_name=Nodo 1 (Principal)"
    set "target_ip=%NODE2_IP%"
    echo 🖥️  Configurado como: %node_name%
    echo 🎯 Nodo objetivo: %target_ip%:18333
) else if "%CURRENT_NODE%"=="2" (
    set "node_type=2"
    set "node_name=Nodo 2 (Secundario)"
    set "target_ip=%NODE1_IP%"
    echo 🖥️  Configurado como: %node_name%
    echo 🎯 Nodo objetivo: %target_ip%:18333
) else (
    echo ❌ CURRENT_NODE debe ser 1 o 2 en .env.local
    pause
    exit /b 1
)



echo.
echo 🚀 Iniciando %node_name%...

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

REM Configurar variables de entorno
set PLAYERGOLD_ENV=testnet
set PLAYERGOLD_CONFIG=config/testnet/node%node_type%.yaml
set PLAYERGOLD_DATA_DIR=data/testnet/node%node_type%

REM Iniciar el nodo correspondiente
if "%node_type%"=="1" (
    echo 🟢 Iniciando Nodo 1...
    start "PlayerGold Nodo 1" cmd /k "python.exe scripts/start_testnet_node.py --node-id validator-node-1 --config config/testnet/node1.yaml --validator --genesis-file data/testnet/genesis.json"
) else (
    echo 🟢 Iniciando Nodo 2...
    start "PlayerGold Nodo 2" cmd /k "python.exe scripts/start_testnet_node.py --node-id validator-node-2 --config config/testnet/node2.yaml --validator --genesis-file data/testnet/genesis.json"
)

echo.
echo ⏳ Esperando 10 segundos para que el nodo se inicie...
timeout /t 10 /nobreak >nul

echo.
echo 🔍 Verificando estado del nodo...

REM Verificar que el nodo está escuchando
netstat -ano | findstr :18333 | findstr LISTENING >nul
if %errorLevel% == 0 (
    echo ✅ Nodo local está escuchando en puerto 18333
) else (
    echo ❌ Nodo local NO está escuchando en puerto 18333
    echo 💡 Verificar la ventana del nodo para errores
    pause
    exit /b 1
)

echo.
echo 🔍 Probando conectividad al nodo remoto...

REM Probar conectividad al nodo remoto
python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(('%target_ip%', 18333))
    sock.close()
    if result == 0:
        print('✅ Conectividad exitosa al nodo remoto %target_ip%:18333')
        sys.exit(0)
    else:
        print('❌ No se puede conectar al nodo remoto %target_ip%:18333')
        sys.exit(1)
except Exception as e:
    print(f'❌ Error probando conectividad: {e}')
    sys.exit(1)
"

if %errorLevel% == 0 (
    echo.
    echo 🎉 ¡RED TESTNET INICIADA EXITOSAMENTE!
    echo.
    echo 📋 ESTADO ACTUAL:
    echo    ✅ %node_name% ejecutándose
    echo    ✅ Puerto 18333 abierto
    echo    ✅ Conectividad al nodo remoto
    echo.
    echo 💡 Los nodos deberían conectarse automáticamente en 30-60 segundos
    echo 💡 Verifica los logs en las ventanas de los nodos
    echo.
    echo 🎮 PRÓXIMOS PASOS:
    echo    1. Abrir wallet: cd wallet ^&^& .\clear-cache-and-start.bat
    echo    2. Descargar modelo IA en la pestaña Minería
    echo    3. Iniciar minería con el modelo descargado
) else (
    echo.
    echo ⚠️  PROBLEMA DE CONECTIVIDAD DETECTADO
    echo.
    echo 🔧 POSIBLES SOLUCIONES:
    echo    1. Verificar que el nodo remoto esté ejecutándose en %target_ip%
    echo    2. Ejecutar este script en la otra máquina (%target_ip%)
    echo    3. Verificar conectividad de red: ping %target_ip%
    echo    4. Configurar firewall en ambas máquinas
    echo.
    echo 📋 COMANDOS ÚTILES:
    echo    - Diagnóstico: python scripts\diagnosticar_conexion_nodos.py
    echo    - Verificar puerto: python scripts\diagnosticar_puerto_ocupado.py
    echo    - Liberar puerto: scripts\liberar_puerto_18333.bat
)

echo.
echo 📊 Para monitorear la red:
echo    python scripts\verificar_estado_red.py

echo.
pause