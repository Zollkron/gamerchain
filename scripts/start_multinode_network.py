#!/usr/bin/env python3
"""
PlayerGold Multi-Node Network Launcher

Launches a complete multi-node PlayerGold network with:
- Bootstrap manager for genesis block creation
- Multi-node PoAIP consensus
- P2P networking with public IP validation
- Automatic reward distribution and halving
- Fee distribution (30% dev, 10% pool, 60% burn)

Usage:
    python scripts/start_multinode_network.py --node-id NODE_ID [--port PORT] [--network testnet|mainnet]
"""

import asyncio
import sys
import logging
import argparse
import signal
from typing import List
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.p2p.network import P2PNetwork
from src.blockchain.enhanced_blockchain import EnhancedBlockchain
from src.consensus.bootstrap_manager import BootstrapManager
from src.consensus.multinode_consensus import MultiNodeConsensus
from src.network.network_manager import NetworkManager, NetworkType
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiNodeNetworkNode:
    """
    Complete multi-node network node implementation
    """
    
    def __init__(self, node_id: str, port: int = None, network_type: str = "testnet", bootstrap_nodes: List[str] = None):
        self.node_id = node_id
        self.network_type = network_type
        self.port = port or (18080 if network_type == "testnet" else 18081)
        
        # Initialize components
        self.network_manager = NetworkManager()
        self.network_manager.set_current_network(NetworkType.TESTNET if network_type == "testnet" else NetworkType.MAINNET)
        
        # Add bootstrap nodes if provided
        if bootstrap_nodes:
            for node_address in bootstrap_nodes:
                self.network_manager.add_bootstrap_node(node_address)
        
        self.blockchain = EnhancedBlockchain()
        self.p2p_network = P2PNetwork(
            node_id=node_id,
            listen_port=self.port,
            network_manager=self.network_manager
        )
        
        self.bootstrap_manager = BootstrapManager(
            p2p_network=self.p2p_network,
            blockchain=self.blockchain,
            network_type=network_type
        )
        
        self.consensus = MultiNodeConsensus(
            node_id=node_id,
            p2p_network=self.p2p_network,
            blockchain=self.blockchain,
            bootstrap_manager=self.bootstrap_manager
        )
        
        # Flask API
        self.api_app = None
        self.api_port = self.port + 1000  # API on port + 1000
        
        # State
        self.running = False
        
        logger.info(f"Multi-Node Network Node initialized: {node_id}")
        logger.info(f"Network: {network_type}")
        logger.info(f"P2P Port: {self.port}")
        logger.info(f"API Port: {self.api_port}")
    
    def create_api_app(self):
        """Create Flask API application"""
        app = Flask(__name__)
        
        @app.route('/api/v1/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'node_id': self.node_id,
                'network': self.network_type,
                'timestamp': datetime.utcnow().isoformat(),
                'version': '2.0.0-multinode',
                'blockchain_height': len(self.blockchain.chain),
                'peer_count': self.p2p_network.get_peer_count(),
                'genesis_created': self.bootstrap_manager.genesis_created
            })
        
        @app.route('/api/v1/network/status', methods=['GET'])
        def network_status():
            consensus_status = self.consensus.get_consensus_status()
            bootstrap_status = self.bootstrap_manager.get_genesis_status()
            
            return jsonify({
                'node_id': self.node_id,
                'network': self.network_type,
                'blockchain': {
                    'height': len(self.blockchain.chain),
                    'latest_block_hash': self.blockchain.get_latest_block().hash,
                    'latest_block_timestamp': self.blockchain.get_latest_block().timestamp
                },
                'p2p': {
                    'peer_count': self.p2p_network.get_peer_count(),
                    'connected_peers': [peer.peer_id for peer in self.p2p_network.get_peer_list()],
                    'network_stats': self.p2p_network.get_network_stats()
                },
                'consensus': consensus_status,
                'bootstrap': bootstrap_status,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @app.route('/api/v1/balance/<address>', methods=['GET'])
        def get_balance(address):
            balance = self.blockchain.get_balance(address)
            return jsonify({
                'success': True,
                'address': address,
                'balance': str(balance),
                'network': self.network_type,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @app.route('/api/v1/transactions/history/<address>', methods=['GET'])
        def get_transaction_history(address):
            history = self.blockchain.get_transaction_history(address)
            
            return jsonify({
                'success': True,
                'address': address,
                'transactions': history,
                'total': len(history),
                'network': self.network_type,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @app.route('/api/v1/blockchain/stats', methods=['GET'])
        def blockchain_stats():
            stats = self.blockchain.get_network_stats()
            return jsonify({
                'success': True,
                'network_stats': stats,
                'network': self.network_type,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @app.route('/api/v1/faucet', methods=['POST'])
        def faucet():
            try:
                if not self.bootstrap_manager.genesis_created:
                    return jsonify({'error': 'Genesis block not created yet'}), 400
                
                data = request.get_json()
                if not data or 'address' not in data:
                    return jsonify({'error': 'Address required'}), 400
                
                address = data['address']
                amount = data.get('amount', 1000)
                
                # Create faucet transaction
                from src.blockchain.enhanced_blockchain import Transaction
                from decimal import Decimal
                
                faucet_tx = Transaction(
                    from_address=self.bootstrap_manager.system_addresses.liquidity_pool,
                    to_address=address,
                    amount=Decimal(str(amount)),
                    fee=Decimal('0'),
                    transaction_type="FAUCET_TRANSFER",
                    memo=f"Testnet faucet - {amount} PRGLD"
                )
                
                # Add to consensus for processing
                self.consensus.add_transaction(faucet_tx)
                
                return jsonify({
                    'success': True,
                    'amount': amount,
                    'address': address,
                    'message': f'Faucet request submitted: {amount} PRGLD to {address}',
                    'note': 'Transaction will be processed in the next block'
                })
                
            except Exception as e:
                logger.error(f"Faucet error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/v1/bootstrap/reset', methods=['POST'])
        def reset_blockchain():
            try:
                data = request.get_json()
                requesting_node = data.get('node_id', self.node_id)
                
                # Run async function in event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.bootstrap_manager.reset_blockchain(requesting_node)
                )
                loop.close()
                
                if result['success']:
                    return jsonify(result)
                else:
                    return jsonify(result), 403
                    
            except Exception as e:
                logger.error(f"Reset error: {e}")
                return jsonify({'error': str(e)}), 500
        
        return app
    
    async def start(self):
        """Start the multi-node network node"""
        try:
            logger.info("=" * 80)
            logger.info("🚀 STARTING PLAYERGOLD MULTI-NODE NETWORK")
            logger.info("=" * 80)
            logger.info(f"🆔 Node ID: {self.node_id}")
            logger.info(f"🌐 Network: {self.network_type}")
            logger.info(f"📡 P2P Port: {self.port}")
            logger.info(f"🔗 API Port: {self.api_port}")
            logger.info("=" * 80)
            
            self.running = True
            
            # Start P2P network
            logger.info("📡 Starting P2P network...")
            await self.p2p_network.start()
            
            # Start bootstrap manager
            logger.info("🏗️  Starting bootstrap manager...")
            await self.bootstrap_manager.start()
            
            # Start consensus system
            logger.info("🤝 Starting consensus system...")
            await self.consensus.start()
            
            # Create and start API server
            logger.info("🌐 Starting API server...")
            self.api_app = self.create_api_app()
            
            # Start API server in background with improved error handling
            import threading
            import time
            
            def run_flask_app():
                try:
                    logger.info(f"🌐 Flask server starting on 0.0.0.0:{self.api_port}")
                    
                    # Test if port is available
                    import socket
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.settimeout(1)
                    result = test_socket.connect_ex(('127.0.0.1', self.api_port))
                    test_socket.close()
                    
                    if result == 0:
                        logger.error(f"❌ Port {self.api_port} is already in use!")
                        return
                    
                    # Start Flask with proper configuration
                    from werkzeug.serving import make_server
                    server = make_server('0.0.0.0', self.api_port, self.api_app, threaded=True)
                    logger.info(f"✅ Flask server ready on 0.0.0.0:{self.api_port}")
                    server.serve_forever()
                    
                except Exception as e:
                    logger.error(f"❌ Flask server error: {e}")
                    import traceback
                    traceback.print_exc()
            
            api_thread = threading.Thread(target=run_flask_app, daemon=True)
            api_thread.start()
            
            # Give Flask more time to start and verify it's working
            await asyncio.sleep(3)
            
            # Test API server
            try:
                import urllib.request
                import urllib.error
                
                req = urllib.request.Request(f"http://127.0.0.1:{self.api_port}/api/v1/health")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        logger.info("✅ API server is responding correctly")
                    else:
                        logger.warning(f"⚠️ API server responded with status {response.status}")
            except urllib.error.URLError as e:
                logger.warning(f"⚠️ Could not verify API server: {e}")
                logger.info("API server may still be starting up...")
            except Exception as e:
                logger.warning(f"⚠️ Could not verify API server: {e}")
                logger.info("API server may still be starting up...")
            
            logger.info("✅ Multi-Node Network started successfully!")
            logger.info(f"🌐 API available at: http://127.0.0.1:{self.api_port}")
            logger.info(f"📊 Network status: http://127.0.0.1:{self.api_port}/api/v1/network/status")
            logger.info(f"💊 Health check: http://127.0.0.1:{self.api_port}/api/v1/health")
            
            # Wait for genesis or continue operation
            if not self.bootstrap_manager.genesis_created:
                logger.info("⏳ Waiting for genesis block creation...")
                logger.info("   Need exactly 2 pioneer AI nodes to create genesis block")
            else:
                logger.info("✅ Genesis block already exists, operating normally")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error starting multi-node network: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def stop(self):
        """Stop the multi-node network node"""
        logger.info("🛑 Stopping multi-node network...")
        
        self.running = False
        
        # Stop components
        await self.p2p_network.stop()
        
        logger.info("✅ Multi-node network stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PlayerGold Multi-Node Network')
    parser.add_argument('--node-id', required=True, help='Unique node identifier')
    parser.add_argument('--port', type=int, help='P2P port (default: 18080 for testnet, 18081 for mainnet)')
    parser.add_argument('--network', choices=['testnet', 'mainnet'], default='testnet', help='Network type')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Log level')
    parser.add_argument('--bootstrap', action='append', help='Bootstrap node address (format: ip:port)')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and start node
    node = MultiNodeNetworkNode(
        node_id=args.node_id,
        port=args.port,
        network_type=args.network,
        bootstrap_nodes=args.bootstrap or []
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, node.handle_signal)
    signal.signal(signal.SIGTERM, node.handle_signal)
    
    try:
        await node.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await node.stop()


if __name__ == "__main__":
    asyncio.run(main())