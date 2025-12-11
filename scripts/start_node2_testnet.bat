@echo off
REM PlayerGold Testnet Node 2 Startup Script
REM IP: 192.168.1.132

echo Starting PlayerGold Testnet Node 2...
echo IP: 192.168.1.132
echo Network: playergold-testnet-genesis

cd /d "%~dp0\.."

REM Set environment variables
set PLAYERGOLD_ENV=testnet
set PLAYERGOLD_CONFIG=config/testnet/node2.yaml
set PLAYERGOLD_DATA_DIR=data/testnet/node2

REM Start node
python.exe scripts/start_testnet_node.py ^
    --node-id validator-node-2 ^
    --config config/testnet/node2.yaml ^
    --validator ^
    --genesis-file data/testnet/genesis.json

echo Node 2 stopped
pause
