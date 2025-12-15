@echo off 
chcp 65001 >nul 
cd /d "%~dp0" 
 
echo ======================================== 
echo 🚀 NODO GÉNESIS 2 - USANDO COORDINADOR
echo ======================================== 
echo. 
echo 📍 Configuración: 
echo   🌐 P2P Puerto: 18081 
echo   🔗 API Puerto: 19081 
echo   🎯 Rol: Nodo Pionero 2 
echo   🌐 Descubrimiento: Network Coordinator (playergold.es)
echo   🔍 Buscará automáticamente otros nodos pioneros
echo. 
echo ✅ SIN IPs hardcodeadas - usa coordinador inteligente
echo.
 
echo 🐍 Iniciando proceso Python del nodo... 
python scripts\start_multinode_network.py --node-id genesis_node_2 --port 18081 --network testnet --log-level INFO
 
pause