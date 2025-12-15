@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 🚀 INICIAR ESCENARIO DE DOS NODOS GÉNESIS
echo ========================================
echo.
echo 🎯 Configuración del escenario:
echo   📍 Nodo 1 (Escritorio): Puerto P2P 18080, API 19080
echo   📍 Nodo 2 (Portátil): Puerto P2P 18081, API 19081
echo.

REM Verificar si hay procesos ocupando los puertos
echo 🔍 Verificando puertos disponibles...

netstat -an | findstr ":18080" >nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  Puerto 18080 ya está en uso
    echo 🔧 Liberando puerto 18080...
    
    REM Encontrar y terminar procesos en puerto 18080
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":18080"') do (
        echo 🛑 Terminando proceso %%a en puerto 18080
        taskkill /PID %%a /F >nul 2>&1
    )
) else (
    echo ✅ Puerto 18080 disponible
)

netstat -an | findstr ":18081" >nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  Puerto 18081 ya está en uso
    echo 🔧 Liberando puerto 18081...
    
    REM Encontrar y terminar procesos en puerto 18081
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":18081"') do (
        echo 🛑 Terminando proceso %%a en puerto 18081
        taskkill /PID %%a /F >nul 2>&1
    )
) else (
    echo ✅ Puerto 18081 disponible
)

netstat -an | findstr ":19080" >nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  Puerto 19080 ya está en uso
    echo 🔧 Liberando puerto 19080...
    
    REM Encontrar y terminar procesos en puerto 19080
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":19080"') do (
        echo 🛑 Terminando proceso %%a en puerto 19080
        taskkill /PID %%a /F >nul 2>&1
    )
) else (
    echo ✅ Puerto 19080 disponible
)

netstat -an | findstr ":19081" >nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  Puerto 19081 ya está en uso
    echo 🔧 Liberando puerto 19081...
    
    REM Encontrar y terminar procesos en puerto 19081
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":19081"') do (
        echo 🛑 Terminando proceso %%a en puerto 19081
        taskkill /PID %%a /F >nul 2>&1
    )
) else (
    echo ✅ Puerto 19081 disponible
)

echo.
echo 🔧 Limpiando datos previos...

REM Limpiar datos de nodos previos
if exist "data\testnet" (
    rmdir /s /q "data\testnet" 2>nul
    echo ✅ Datos de testnet limpiados
)

if exist "data\node_id.txt" (
    del /f "data\node_id.txt" 2>nul
    echo ✅ Node ID limpiado
)

if exist "logs" (
    del /q "logs\*.log" 2>nul
    echo ✅ Logs limpiados
)

echo.
echo ========================================
echo 🎮 INSTRUCCIONES PARA EL ESCENARIO
echo ========================================
echo.
echo 📋 PASO 1: NODO 1 (ESCRITORIO - ESTE EQUIPO)
echo   1️⃣ Ejecutar: start-node1-genesis.bat
echo   2️⃣ Esperar a que aparezca: "Waiting for exactly 2 pioneer AI nodes"
echo   3️⃣ Verificar que P2P esté en puerto 18080
echo.
echo 📋 PASO 2: NODO 2 (PORTÁTIL - OTRO EQUIPO)
echo   1️⃣ git pull (para obtener los últimos cambios)
echo   2️⃣ Ejecutar: start-node2-genesis.bat
echo   3️⃣ Verificar que P2P esté en puerto 18081
echo   4️⃣ Los nodos se conectarán automáticamente
echo.
echo 📋 PASO 3: CREACIÓN DEL GÉNESIS
echo   ✅ Los nodos se detectarán automáticamente
echo   ✅ Se creará el bloque génesis real
echo   ✅ La blockchain comenzará a funcionar
echo.
echo ⚠️  IMPORTANTE: Ejecuta los nodos EN ORDEN
echo    Primero Nodo 1, luego Nodo 2
echo.

set /p continue="¿Continuar con la creación de scripts específicos? (S/N): "
if /i "%continue%" NEQ "S" (
    echo ❌ Operación cancelada
    goto :end
)

echo.
echo 🔧 Creando scripts específicos para cada nodo...

REM Crear script para Nodo 1
echo @echo off > start-node1-genesis.bat
echo chcp 65001 ^>nul >> start-node1-genesis.bat
echo cd /d "%%~dp0" >> start-node1-genesis.bat
echo. >> start-node1-genesis.bat
echo echo ======================================== >> start-node1-genesis.bat
echo echo 🚀 INICIANDO NODO GÉNESIS 1 ^(ESCRITORIO^) >> start-node1-genesis.bat
echo echo ======================================== >> start-node1-genesis.bat
echo echo. >> start-node1-genesis.bat
echo echo 📍 Configuración: >> start-node1-genesis.bat
echo echo   🌐 P2P Puerto: 18080 >> start-node1-genesis.bat
echo echo   🔗 API Puerto: 19080 >> start-node1-genesis.bat
echo echo   🎯 Rol: Nodo Pionero 1 >> start-node1-genesis.bat
echo echo. >> start-node1-genesis.bat
echo. >> start-node1-genesis.bat
echo echo 🐍 Iniciando proceso Python del nodo... >> start-node1-genesis.bat
echo python scripts\start_multinode_network.py --node-id genesis_node_1 --port 18080 --network testnet --log-level INFO >> start-node1-genesis.bat
echo. >> start-node1-genesis.bat
echo pause >> start-node1-genesis.bat

REM Crear script para Nodo 2
echo @echo off > start-node2-genesis.bat
echo chcp 65001 ^>nul >> start-node2-genesis.bat
echo cd /d "%%~dp0" >> start-node2-genesis.bat
echo. >> start-node2-genesis.bat
echo echo ======================================== >> start-node2-genesis.bat
echo echo 🚀 INICIANDO NODO GÉNESIS 2 ^(PORTÁTIL^) >> start-node2-genesis.bat
echo echo ======================================== >> start-node2-genesis.bat
echo echo. >> start-node2-genesis.bat
echo echo 📍 Configuración: >> start-node2-genesis.bat
echo echo   🌐 P2P Puerto: 18081 >> start-node2-genesis.bat
echo echo   🔗 API Puerto: 19081 >> start-node2-genesis.bat
echo echo   🎯 Rol: Nodo Pionero 2 >> start-node2-genesis.bat
echo echo   🔍 Buscará conectar con Nodo 1 en puerto 18080 >> start-node2-genesis.bat
echo echo. >> start-node2-genesis.bat
echo. >> start-node2-genesis.bat
echo echo 🐍 Iniciando proceso Python del nodo... >> start-node2-genesis.bat
echo python scripts\start_multinode_network.py --node-id genesis_node_2 --port 18081 --network testnet --log-level INFO --bootstrap 127.0.0.1:18080 >> start-node2-genesis.bat
echo. >> start-node2-genesis.bat
echo pause >> start-node2-genesis.bat

echo ✅ Scripts creados:
echo   📄 start-node1-genesis.bat (para este equipo)
echo   📄 start-node2-genesis.bat (para el portátil)

echo.
echo ========================================
echo 🎯 PRÓXIMOS PASOS
echo ========================================
echo.
echo 1️⃣ EN ESTE EQUIPO (ESCRITORIO):
echo    Ejecutar: start-node1-genesis.bat
echo.
echo 2️⃣ EN EL PORTÁTIL:
echo    - git pull
echo    - Copiar start-node2-genesis.bat
echo    - Ejecutar: start-node2-genesis.bat
echo.
echo 3️⃣ RESULTADO ESPERADO:
echo    ✅ Nodo 1 esperará en puerto 18080
echo    ✅ Nodo 2 se conectará desde puerto 18081
echo    ✅ Se creará el bloque génesis automáticamente
echo    ✅ La blockchain comenzará a funcionar
echo.

:end
echo ========================================
echo 🔧 CONFIGURACIÓN COMPLETADA
echo ========================================
pause