@echo off 
chcp 65001 >nul 
cd /d "%~dp0" 
 
echo ======================================== 
echo 🚀 NODO GÉNESIS 1 - ESCRITORIO (RED DOMÉSTICA)
echo ======================================== 
echo. 
echo 📍 Configuración: 
echo   🌐 P2P Puerto: 18080 
echo   🔗 API Puerto: 19080 
echo   🎯 Rol: Nodo Pionero 1 (Escritorio)
echo   🏠 Red: Router doméstico
echo   🌐 Descubrimiento: Network Coordinator (playergold.es)
echo   📡 Se registrará como nodo disponible
echo. 
echo ✅ AUTODISCOVERY ACTIVADO - Sin IPs hardcodeadas
echo ✅ Se registrará automáticamente con el coordinador
echo ✅ Esperará conexión del portátil para crear génesis
echo.

echo 🔍 Verificando dependencias Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado
    pause
    exit /b 1
)

echo.
echo 🌐 Obteniendo IP pública del escritorio...
for /f "delims=" %%i in ('python -c "import requests; print(requests.get('https://api.ipify.org').text.strip())"') do set PUBLIC_IP=%%i
echo 📍 IP pública del escritorio: %PUBLIC_IP%
echo.

echo 🐍 Iniciando proceso Python del nodo... 
echo 📝 El nodo se registrará automáticamente con el coordinador
echo 📡 Esperando conexión del portátil para crear el bloque génesis...
echo.

python scripts\start_multinode_network.py --node-id genesis_node_1_desktop --port 18080 --network testnet --log-level INFO
 
pause