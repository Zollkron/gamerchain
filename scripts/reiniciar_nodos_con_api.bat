@echo off
REM Script para reiniciar nodos con API REST habilitada
setlocal enabledelayedexpansion

echo ============================================================
echo 🔄 REINICIANDO NODOS CON API REST - PLAYERGOLD
echo ============================================================
echo.

REM Cargar configuración desde .env.local
if not exist ".env.local" (
    echo ❌ Archivo .env.local no encontrado
    echo 💡 Ejecuta: python scripts\generar_env_local_auto.py
    pause
    exit /b 1
)

REM Leer variables de entorno desde .env.local
for /f "usebackq tokens=1,2 delims==" %%a in (".env.local") do (
    if "%%a"=="CURRENT_NODE" set "CURRENT_NODE=%%b"
)

if not defined CURRENT_NODE (
    echo ❌ Variable CURRENT_NODE no definida en .env.local
    pause
    exit /b 1
)

echo 🛑 Deteniendo nodos existentes...

REM Intentar cerrar procesos Python de forma elegante
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH') do (
    set "pid=%%i"
    set "pid=!pid:"=!"
    echo 🔄 Cerrando proceso Python PID: !pid!
    taskkill /PID !pid! /T >nul 2>&1
)

echo ⏳ Esperando 3 segundos para que los procesos se cierren...
timeout /t 3 /nobreak >nul

REM Verificar que el puerto esté libre
netstat -ano | findstr :18333 >nul
if %errorLevel% == 0 (
    echo ⚠️  Puerto 18333 aún ocupado, forzando cierre...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18333') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

netstat -ano | findstr :18080 >nul
if %errorLevel% == 0 (
    echo ⚠️  Puerto 18080 aún ocupado, forzando cierre...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18080') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo ⏳ Esperando 2 segundos adicionales...
timeout /t 2 /nobreak >nul

echo.
echo 🚀 Iniciando nodo con API REST...

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

REM Configurar variables de entorno
set PLAYERGOLD_ENV=testnet

REM Iniciar el nodo correspondiente con API
if "%CURRENT_NODE%"=="1" (
    echo 🟢 Iniciando Nodo 1 con API REST...
    start "PlayerGold Nodo 1 + API" cmd /k "python.exe scripts/start_testnet_node.py --node-id validator-node-1 --config config/testnet/node1.yaml --validator --genesis-file data/testnet/genesis.json"
) else (
    echo 🟢 Iniciando Nodo 2 con API REST...
    start "PlayerGold Nodo 2 + API" cmd /k "python.exe scripts/start_testnet_node.py --node-id validator-node-2 --config config/testnet/node2.yaml --validator --genesis-file data/testnet/genesis.json"
)

echo.
echo ⏳ Esperando 10 segundos para que el nodo se inicie...
timeout /t 10 /nobreak >nul

echo.
echo 🔍 Verificando servicios...

REM Verificar P2P
netstat -ano | findstr :18333 | findstr LISTENING >nul
if %errorLevel% == 0 (
    echo ✅ P2P Network: Puerto 18333 activo
) else (
    echo ❌ P2P Network: Puerto 18333 no activo
)

REM Verificar API
netstat -ano | findstr :18080 | findstr LISTENING >nul
if %errorLevel% == 0 (
    echo ✅ REST API: Puerto 18080 activo
) else (
    echo ❌ REST API: Puerto 18080 no activo
)

echo.
echo 🌐 Probando API REST...
python -c "
import requests
import sys
try:
    response = requests.get('http://localhost:18080/api/v1/health', timeout=5)
    if response.status_code == 200:
        print('✅ API REST: Health check exitoso')
        print(f'   Respuesta: {response.json()}')
    else:
        print(f'❌ API REST: Health check falló (status: {response.status_code})')
except Exception as e:
    print(f'❌ API REST: No accesible ({e})')
"

echo.
echo 📊 Estado final:
echo    🔹 Nodo: %CURRENT_NODE%
echo    🔹 P2P: localhost:18333
echo    🔹 API: http://localhost:18080
echo.
echo 💡 Ahora puedes usar las wallets normalmente
echo 💡 Las wallets se conectarán a http://localhost:18080
echo.

pause