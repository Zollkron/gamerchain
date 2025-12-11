@echo off
REM Script seguro para iniciar Nodo 1 - Verifica puerto antes de iniciar
REM IP: Variable de entorno

echo ============================================================
echo 🚀 INICIANDO NODO 1 TESTNET PLAYERGOLD (SEGURO)
echo ============================================================
echo.

echo 🔍 Verificando si puerto 18333 está libre...
netstat -ano | findstr :18333 >nul
if %errorLevel% == 0 (
    echo ❌ Puerto 18333 está ocupado
    echo.
    echo 🔧 Liberando puerto automáticamente...
    
    REM Obtener PID del proceso que usa el puerto
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18333') do (
        echo 🔄 Terminando proceso con PID: %%a
        taskkill /PID %%a /F >nul 2>&1
        if !errorLevel! == 0 (
            echo ✅ Proceso %%a terminado
        ) else (
            echo ⚠️  No se pudo terminar proceso %%a
        )
    )
    
    echo.
    echo ⏳ Esperando 2 segundos para que el puerto se libere...
    timeout /t 2 /nobreak >nul
    
    REM Verificar nuevamente
    netstat -ano | findstr :18333 >nul
    if %errorLevel% == 0 (
        echo ❌ Puerto aún ocupado. Usa scripts\liberar_puerto_18333.bat
        pause
        exit /b 1
    ) else (
        echo ✅ Puerto 18333 ahora está libre
    )
) else (
    echo ✅ Puerto 18333 está libre
)

echo.
echo 🚀 Iniciando Nodo 1 (Principal)...
echo Red: playergold-testnet-genesis
echo Puerto: 18333
echo.

cd /d "%~dp0\.."

REM Set environment variables
set PLAYERGOLD_ENV=testnet
set PLAYERGOLD_CONFIG=config/testnet/node1.yaml
set PLAYERGOLD_DATA_DIR=data/testnet/node1

REM Start node
python.exe scripts/start_testnet_node.py ^
    --node-id validator-node-1 ^
    --config config/testnet/node1.yaml ^
    --validator ^
    --genesis-file data/testnet/genesis.json

echo.
echo 📋 Nodo 1 detenido
echo.
echo 💡 Para reiniciar:
echo    scripts\start_node1_testnet_seguro.bat
echo.
echo 🔍 Para diagnosticar problemas:
echo    python scripts\diagnosticar_puerto_ocupado.py
echo.

pause