@echo off 
chcp 65001 >nul 
cd /d "%~dp0" 
 
echo ======================================== 
echo 🚀 NODO GÉNESIS 2 - PORTÁTIL (RED MÓVIL)
echo ======================================== 
echo. 
echo 📍 Configuración: 
echo   🌐 P2P Puerto: 18081 
echo   🔗 API Puerto: 19081 
echo   🎯 Rol: Nodo Pionero 2 (Portátil)
echo   📱 Red: Datos móviles
echo   🌐 Descubrimiento: Network Coordinator (playergold.es)
echo   🔍 Buscará automáticamente el nodo del escritorio
echo. 
echo ✅ AUTODISCOVERY ACTIVADO - Sin IPs hardcodeadas
echo ✅ Se registrará automáticamente con el coordinador
echo ✅ Obtendrá el mapa de red y se conectará al escritorio
echo.

echo 🔍 Verificando dependencias Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado
    echo 📝 Instala Python desde python.org
    pause
    exit /b 1
)

echo.
echo 🔍 Verificando módulos Python...
python -c "import requests" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Módulo 'requests' no encontrado
    echo 📝 Instalando requests...
    pip install requests
)

python -c "import asyncio" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Módulo 'asyncio' no encontrado (debería estar incluido)
    pause
    exit /b 1
)

echo ✅ Dependencias verificadas
echo.

echo 🌐 Obteniendo IP pública del portátil...
for /f "delims=" %%i in ('python -c "import requests; print(requests.get('https://api.ipify.org').text.strip())"') do set PUBLIC_IP=%%i
echo 📍 IP pública del portátil: %PUBLIC_IP%
echo.

echo 🐍 Iniciando proceso Python del nodo... 
echo 📝 El nodo se registrará automáticamente y buscará peers
echo 📡 Esperando conexión con el nodo del escritorio...
echo.

python scripts\start_multinode_network.py --node-id genesis_node_2_laptop --port 18081 --network testnet --log-level INFO
 
pause