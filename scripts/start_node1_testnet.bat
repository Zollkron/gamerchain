@echo off
# PlayerGold Testnet Node 1 Startup Script
# IP: 192.168.1.129

echo "Starting PlayerGold Testnet Node 1..."
echo "IP: 192.168.1.129"
echo "Network: playergold-testnet-genesis"

cd "$(dirname "$0")/.."

# Set environment
export PLAYERGOLD_ENV=testnet
export PLAYERGOLD_CONFIG=config/testnet/node1.yaml
export PLAYERGOLD_DATA_DIR=data/testnet/node1

# Start node
python.exe scripts/start_testnet_node.py ^
    --node-id validator-node-1 ^
    --config config/testnet/node1.yaml ^
    --validator ^
    --genesis-file data/testnet/genesis.json

echo "Node 1 stopped"
