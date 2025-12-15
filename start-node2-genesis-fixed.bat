@echo off 
chcp 65001 >nul 
cd /d "%~dp0" 
 
echo ======================================== 
echo 🚀 INICIANDO NODO GÉNESIS 2 (PORTÁTIL) - CORREGIDO
echo ======================================== 
echo. 
echo 📍 Configuración: 
echo   🌐 P2P Puerto: 18081 
echo   🔗 API Puerto: 19081 
echo   🎯 Rol: Nodo Pionero 2 
echo   🔍 Conectará con Nodo 1 en: 192.168.1.129:18080
echo. 
 
echo 🐍 Iniciando proceso Python del nodo... 
python scripts\start_multinode_network.py --node-id genesis_node_2 --port 18081 --network testnet --log-level INFO --bootstrap 192.168.1.129:18080
 
pause