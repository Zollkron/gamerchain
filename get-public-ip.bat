@echo off
chcp 65001 >nul

echo ========================================
echo 🌐 DETECTAR IP PÚBLICA DEL ESCRITORIO
echo ========================================
echo.

echo 🔍 Obteniendo IP pública...
echo.

REM Intentar varios servicios para obtener IP pública
echo 📡 Método 1: ipinfo.io
curl -s ipinfo.io/ip 2>nul
if %ERRORLEVEL% EQU 0 echo.

echo.
echo 📡 Método 2: ifconfig.me
curl -s ifconfig.me 2>nul
if %ERRORLEVEL% EQU 0 echo.

echo.
echo 📡 Método 3: icanhazip.com
curl -s icanhazip.com 2>nul
if %ERRORLEVEL% EQU 0 echo.

echo.
echo ========================================
echo ⚠️  CONFIGURACIÓN REQUERIDA
echo ========================================
echo.
echo 🔧 PASOS NECESARIOS:
echo.
echo 1️⃣ CONFIGURAR PORT FORWARDING EN EL ROUTER:
echo    - Puerto: 18080 (TCP)
echo    - IP destino: 192.168.1.129 (IP local del escritorio)
echo    - Protocolo: TCP
echo.
echo 2️⃣ VERIFICAR FIREWALL:
echo    - Permitir puerto 18080 entrante
echo    - Permitir Python en firewall de Windows
echo.
echo 3️⃣ EN EL PORTÁTIL:
echo    - Usar la IP pública mostrada arriba
echo    - Comando: python scripts\start_multinode_network.py --node-id genesis_node_2 --port 18081 --network testnet --log-level INFO --bootstrap [IP_PUBLICA]:18080
echo.
echo 🚨 IMPORTANTE: Sin port forwarding, la conexión fallará
echo.

pause