#!/usr/bin/env python3
"""
Script para configurar el bloque génesis de testnet PlayerGold
Configura dos nodos iniciales como validadores génesis

Uso:
    python scripts/setup_testnet_genesis.py --node1-ip IP1 --node2-ip IP2
"""

import asyncio
import sys
import argparse
import logging
import json
import yaml
from pathlib import Path
from datetime import datetime
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.network.network_manager import NetworkManager, NetworkType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestnetGenesisSetup:
    """Setup testnet genesis configuration"""
    
    def __init__(self, node1_ip: str, node2_ip: str):
        self.node1_ip = node1_ip
        self.node2_ip = node2_ip
        self.genesis_time = datetime.utcnow().isoformat()
        
        # Testnet configuration
        self.testnet_config = {
            'network_id': 'playergold-testnet-genesis',
            'genesis_time': self.genesis_time,
            'initial_validators': [],
            'initial_supply': 1000000,  # 1M PRGLD for testing
            'faucet_amount': 1000,      # 1K PRGLD per faucet request
            'block_time': 10,           # 10 seconds per block
            'consensus': {
                'type': 'PoAIP',
                'min_validators': 2,
                'quorum_percentage': 0.66
            }
        }
    
    async def setup_genesis(self):
        """Setup genesis configuration for testnet"""
        logger.info("=" * 60)
        logger.info("PlayerGold Testnet Genesis Setup")
        logger.info("=" * 60)
        
        # Create data directories
        await self._create_directories()
        
        # Generate validator wallets
        validator1 = await self._generate_validator_wallet("validator-node-1", self.node1_ip)
        validator2 = await self._generate_validator_wallet("validator-node-2", self.node2_ip)
        
        # Add validators to genesis
        self.testnet_config['initial_validators'] = [validator1, validator2]
        
        # Create genesis block
        genesis_block = await self._create_genesis_block()
        
        # Save configurations
        await self._save_configurations(genesis_block)
        
        # Generate node startup scripts
        await self._generate_startup_scripts()
        
        logger.info("=" * 60)
        logger.info("✓ Testnet Genesis Setup Complete!")
        logger.info("=" * 60)
        logger.info(f"Genesis Time: {self.genesis_time}")
        logger.info(f"Network ID: {self.testnet_config['network_id']}")
        logger.info(f"Initial Validators: 2")
        logger.info(f"Initial Supply: {self.testnet_config['initial_supply']:,} PRGLD")
        logger.info("")
        logger.info("Next Steps:")
        logger.info("1. Copy configurations to both nodes")
        logger.info("2. Run startup scripts on both machines")
        logger.info("3. Verify network connectivity")
        logger.info("4. Test faucet and transactions")
        logger.info("=" * 60)
        
        return {
            'genesis_block': genesis_block,
            'validators': [validator1, validator2],
            'config': self.testnet_config
        }
    
    async def _create_directories(self):
        """Create necessary directories"""
        directories = [
            'data/testnet',
            'data/testnet/node1',
            'data/testnet/node2',
            'config/testnet',
            'wallets/testnet'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    async def _generate_validator_wallet(self, node_name: str, ip_address: str):
        """Generate validator wallet for genesis"""
        # Simulate wallet generation (in real implementation, use WalletService)
        import secrets
        
        # Generate deterministic but secure keys for testnet
        seed = f"{node_name}-{ip_address}-{self.genesis_time}"
        hash_obj = hashlib.sha256(seed.encode())
        private_key = hash_obj.hexdigest()
        
        # Generate address (simplified)
        address_hash = hashlib.sha256(private_key.encode()).hexdigest()
        address = f"PG{address_hash[:38]}"
        
        validator = {
            'node_name': node_name,
            'address': address,
            'ip_address': ip_address,
            'port': 18333,
            'stake': 100000,  # 100K PRGLD stake
            'is_genesis_validator': True,
            'public_key': f"pub_{private_key[:32]}",
            'created_at': self.genesis_time
        }
        
        # Save wallet info (without private key in config)
        wallet_file = f"wallets/testnet/{node_name}.json"
        wallet_data = {
            **validator,
            'private_key': private_key,  # Only in wallet file
            'mnemonic': f"testnet genesis validator {node_name} seed phrase for development only"
        }
        
        with open(wallet_file, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        logger.info(f"Generated validator wallet: {node_name}")
        logger.info(f"  Address: {address}")
        logger.info(f"  IP: {ip_address}")
        logger.info(f"  Stake: {validator['stake']:,} PRGLD")
        
        return validator
    
    async def _create_genesis_block(self):
        """Create the genesis block"""
        genesis_block = {
            'block_number': 0,
            'previous_hash': '0' * 64,
            'timestamp': self.genesis_time,
            'merkle_root': self._calculate_genesis_merkle_root(),
            'validator': self.testnet_config['initial_validators'][0]['address'],
            'transactions': self._create_genesis_transactions(),
            'consensus_data': {
                'type': 'PoAIP',
                'validators': [v['address'] for v in self.testnet_config['initial_validators']],
                'quorum_achieved': True,
                'signatures': []
            },
            'network_id': self.testnet_config['network_id'],
            'version': '1.0.0'
        }
        
        # Calculate block hash
        block_string = json.dumps(genesis_block, sort_keys=True)
        genesis_block['hash'] = hashlib.sha256(block_string.encode()).hexdigest()
        
        logger.info(f"Created genesis block: {genesis_block['hash'][:16]}...")
        
        return genesis_block
    
    def _create_genesis_transactions(self):
        """Create initial transactions for genesis block"""
        transactions = []
        
        # Initial token distribution
        for validator in self.testnet_config['initial_validators']:
            tx = {
                'type': 'genesis_allocation',
                'to_address': validator['address'],
                'amount': validator['stake'],
                'timestamp': self.genesis_time,
                'memo': f"Genesis allocation for {validator['node_name']}"
            }
            transactions.append(tx)
        
        # Faucet allocation
        faucet_address = "PGfaucet" + "0" * 33  # Faucet address
        faucet_tx = {
            'type': 'genesis_allocation',
            'to_address': faucet_address,
            'amount': 500000,  # 500K PRGLD for faucet
            'timestamp': self.genesis_time,
            'memo': 'Testnet faucet allocation'
        }
        transactions.append(faucet_tx)
        
        return transactions
    
    def _calculate_genesis_merkle_root(self):
        """Calculate merkle root for genesis transactions"""
        # Simplified merkle root calculation
        transactions = self._create_genesis_transactions()
        tx_hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() 
                    for tx in transactions]
        
        if not tx_hashes:
            return '0' * 64
        
        # Simple merkle root (in production, use proper merkle tree)
        combined = ''.join(tx_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    async def _save_configurations(self, genesis_block):
        """Save all configuration files"""
        
        # Save genesis block
        with open('data/testnet/genesis.json', 'w') as f:
            json.dump(genesis_block, f, indent=2)
        
        # Save testnet config
        with open('config/testnet/testnet.yaml', 'w') as f:
            yaml.dump(self.testnet_config, f, indent=2)
        
        # Create node-specific configs
        for i, validator in enumerate(self.testnet_config['initial_validators'], 1):
            node_config = {
                'node': {
                    'node_id': validator['node_name'],
                    'validator_address': validator['address'],
                    'is_validator': True,
                    'data_dir': f'./data/testnet/node{i}'
                },
                'network': {
                    'network_type': 'testnet',
                    'network_id': self.testnet_config['network_id'],
                    'listen_ip': '0.0.0.0',
                    'listen_port': 18333,
                    'external_ip': validator['ip_address'],
                    'bootstrap_nodes': [
                        f"{self.node1_ip}:18333",
                        f"{self.node2_ip}:18333"
                    ]
                },
                'consensus': self.testnet_config['consensus'],
                'genesis_file': '../genesis.json'
            }
            
            with open(f'config/testnet/node{i}.yaml', 'w') as f:
                yaml.dump(node_config, f, indent=2)
        
        logger.info("Saved configuration files:")
        logger.info("  - data/testnet/genesis.json")
        logger.info("  - config/testnet/testnet.yaml")
        logger.info("  - config/testnet/node1.yaml")
        logger.info("  - config/testnet/node2.yaml")
    
    async def _generate_startup_scripts(self):
        """Generate startup scripts for each node"""
        
        # Node 1 startup script
        node1_script = f"""#!/bin/bash
# PlayerGold Testnet Node 1 Startup Script
# IP: {self.node1_ip}

echo "Starting PlayerGold Testnet Node 1..."
echo "IP: {self.node1_ip}"
echo "Network: {self.testnet_config['network_id']}"

cd "$(dirname "$0")/.."

# Set environment
export PLAYERGOLD_ENV=testnet
export PLAYERGOLD_CONFIG=config/testnet/node1.yaml
export PLAYERGOLD_DATA_DIR=data/testnet/node1

# Start node
python scripts/start_testnet_node.py \\
    --node-id validator-node-1 \\
    --config config/testnet/node1.yaml \\
    --validator \\
    --genesis-file data/testnet/genesis.json

echo "Node 1 stopped"
"""
        
        # Node 2 startup script
        node2_script = f"""#!/bin/bash
# PlayerGold Testnet Node 2 Startup Script
# IP: {self.node2_ip}

echo "Starting PlayerGold Testnet Node 2..."
echo "IP: {self.node2_ip}"
echo "Network: {self.testnet_config['network_id']}"

cd "$(dirname "$0")/.."

# Set environment
export PLAYERGOLD_ENV=testnet
export PLAYERGOLD_CONFIG=config/testnet/node2.yaml
export PLAYERGOLD_DATA_DIR=data/testnet/node2

# Start node
python scripts/start_testnet_node.py \\
    --node-id validator-node-2 \\
    --config config/testnet/node2.yaml \\
    --validator \\
    --genesis-file data/testnet/genesis.json

echo "Node 2 stopped"
"""
        
        # Windows batch files
        node1_bat = node1_script.replace('#!/bin/bash', '@echo off').replace('\\', '^')
        node1_bat = node1_bat.replace('python', 'python.exe')
        
        node2_bat = node2_script.replace('#!/bin/bash', '@echo off').replace('\\', '^')
        node2_bat = node2_bat.replace('python', 'python.exe')
        
        # Save scripts
        with open('scripts/start_node1_testnet.sh', 'w') as f:
            f.write(node1_script)
        
        with open('scripts/start_node2_testnet.sh', 'w') as f:
            f.write(node2_script)
        
        with open('scripts/start_node1_testnet.bat', 'w') as f:
            f.write(node1_bat)
        
        with open('scripts/start_node2_testnet.bat', 'w') as f:
            f.write(node2_bat)
        
        # Make shell scripts executable
        import os
        os.chmod('scripts/start_node1_testnet.sh', 0o755)
        os.chmod('scripts/start_node2_testnet.sh', 0o755)
        
        logger.info("Generated startup scripts:")
        logger.info("  - scripts/start_node1_testnet.sh/.bat")
        logger.info("  - scripts/start_node2_testnet.sh/.bat")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Setup PlayerGold testnet genesis configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_testnet_genesis.py --node1-ip 192.168.1.100 --node2-ip 192.168.1.101
  python scripts/setup_testnet_genesis.py --node1-ip 10.0.0.10 --node2-ip 10.0.0.11
        """
    )
    
    parser.add_argument(
        '--node1-ip',
        type=str,
        required=True,
        help='IP address of the first validator node'
    )
    
    parser.add_argument(
        '--node2-ip',
        type=str,
        required=True,
        help='IP address of the second validator node'
    )
    
    args = parser.parse_args()
    
    try:
        setup = TestnetGenesisSetup(args.node1_ip, args.node2_ip)
        result = await setup.setup_genesis()
        
        print("\n" + "=" * 60)
        print("🎉 TESTNET GENESIS SETUP COMPLETE!")
        print("=" * 60)
        print(f"Genesis Block Hash: {result['genesis_block']['hash']}")
        print(f"Network ID: {result['config']['network_id']}")
        print(f"Validators: {len(result['validators'])}")
        print("\nValidator Addresses:")
        for validator in result['validators']:
            print(f"  {validator['node_name']}: {validator['address']}")
        print("\nNext: Copy files to both nodes and run startup scripts!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error setting up testnet genesis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())