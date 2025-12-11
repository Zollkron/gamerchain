#!/bin/bash
# PlayerGold Testnet Node 2 Startup Script
# IP: 192.168.1.132

echo "Starting PlayerGold Testnet Node 2..."
echo "IP: 192.168.1.132"
echo "Network: playergold-testnet-genesis"

cd "$(dirname "$0")/.."

# Set environment
export PLAYERGOLD_ENV=testnet
export PLAYERGOLD_CONFIG=config/testnet/node2.yaml
export PLAYERGOLD_DATA_DIR=data/testnet/node2

# Start node
python scripts/start_testnet_node.py \
    --node-id validator-node-2 \
    --config config/testnet/node2.yaml \
    --validator \
    --genesis-file data/testnet/genesis.json

echo "Node 2 stopped"
