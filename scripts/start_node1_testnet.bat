@echo off
REM PlayerGold Testnet Node 1 Startup Script
REM IP: 192.168.1.129

echo Starting PlayerGold Testnet Node 1...
echo IP: 192.168.1.129
echo Network: playergold-testnet-genesis

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

echo Node 1 stopped
pause
