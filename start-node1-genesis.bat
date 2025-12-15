@echo off 
chcp 65001 >nul 
cd /d "%~dp0" 
 
echo ======================================== 
echo 🚀 INICIANDO NODO GÉNESIS 1 (ESCRITORIO) 
echo ======================================== 
echo. 
echo 📍 Configuración: 
echo   🌐 P2P Puerto: 18080 
echo   🔗 API Puerto: 19080 
echo   🎯 Rol: Nodo Pionero 1 
echo. 
 
echo 🐍 Iniciando proceso Python del nodo... 
python scripts\start_multinode_network.py --node-id genesis_node_1 --port 18080 --network testnet --log-level INFO 
 
pause 
