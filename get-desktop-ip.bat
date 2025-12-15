@echo off
chcp 65001 >nul

echo ========================================
echo 🔍 DETECTAR IP DEL ESCRITORIO
echo ========================================
echo.

echo 📡 IPs disponibles en este equipo:
ipconfig | findstr "IPv4"

echo.
echo 🎯 Para el escenario de dos nodos:
echo.
echo 📋 INSTRUCCIONES:
echo   1️⃣ Identifica la IP de la red local (normalmente 192.168.x.x)
echo   2️⃣ En el portátil, usa esa IP en lugar de 127.0.0.1
echo   3️⃣ Comando correcto para el portátil:
echo.
echo      python scripts\start_multinode_network.py --node-id genesis_node_2 --port 18081 --network testnet --log-level INFO --bootstrap [IP_DEL_ESCRITORIO]:18080
echo.
echo 🔧 Ejemplo con IP 192.168.1.129:
echo      python scripts\start_multinode_network.py --node-id genesis_node_2 --port 18081 --network testnet --log-level INFO --bootstrap 192.168.1.129:18080
echo.

pause