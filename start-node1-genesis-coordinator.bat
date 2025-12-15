@echo off 
chcp 65001 >nul 
cd /d "%~dp0" 
 
echo ======================================== 
echo 🚀 NODO GÉNESIS 1 - USANDO COORDINADOR
echo ======================================== 
echo. 
echo 📍 Configuración: 
echo   🌐 P2P Puerto: 18080 
echo   🔗 API Puerto: 19080 
echo   🎯 Rol: Nodo Pionero 1 
echo   🌐 Registro: Network Coordinator (playergold.es)
echo   📡 Se registrará como nodo disponible
echo. 
echo ✅ SIN IPs hardcodeadas - usa coordinador inteligente
echo.
 
echo 🐍 Iniciando proceso Python del nodo... 
python scripts\start_multinode_network.py --node-id genesis_node_1 --port 18080 --network testnet --log-level INFO
 
pause