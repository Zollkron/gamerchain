#!/usr/bin/env python3
"""
Script para iniciar un nodo PlayerGold en TESTNET

Testnet es seguro para desarrollo y pruebas:
- Tokens sin valor real
- Blockchain puede ser reseteada
- Perfecto para experimentar

Uso:
    python scripts/start_testnet_node.py [--node-id NODE_ID] [--port PORT]
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.network.network_manager import NetworkManager, NetworkType
from src.p2p.network import P2PNetwork
from src.api.game_api import GameAPI
from src.blockchain.blockchain import Blockchain
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_testnet_node(node_id: str, port: int = None, config_file: str = None, 
                           is_validator: bool = False, genesis_file: str = None):
    """
    Start a testnet node
    
    Args:
        node_id: Unique identifier for this node
        port: Optional custom port (uses 18333 by default)
        config_file: Configuration file path
        is_validator: Whether this node is a validator
        genesis_file: Genesis block file path
    """
    logger.info("=" * 60)
    logger.info("PlayerGold Testnet Node")
    logger.info("=" * 60)
    logger.info("")
    
    # Configure for testnet
    network_manager = NetworkManager()
    
    # Ensure we're on testnet
    if not network_manager.is_testnet():
        logger.info("Switching to testnet...")
        network_manager.switch_network(NetworkType.TESTNET)
    
    # Get network info
    network_info = network_manager.get_network_info()
    
    # Load configuration if provided
    if config_file:
        logger.info(f"Loading configuration from: {config_file}")
        # TODO: Load actual configuration
    
    # Load genesis file if provided
    if genesis_file:
        logger.info(f"Loading genesis block from: {genesis_file}")
        # TODO: Load and validate genesis block
    
    logger.info("Network Configuration:")
    logger.info(f"  Type: TESTNET")
    logger.info(f"  Network ID: {network_info['network_id']}")
    logger.info(f"  Default Port: {network_info['p2p_port']}")
    logger.info(f"  Bootstrap Nodes: {network_info['bootstrap_nodes']}")
    logger.info(f"  Validator Mode: {'Yes' if is_validator else 'No'}")
    logger.info("")
    
    logger.info("⚠️  Testnet Information:")
    logger.info("  ✓ Tokens have NO real value")
    logger.info("  ✓ Blockchain can be reset")
    logger.info("  ✓ Safe for testing and development")
    logger.info("  ✓ Data stored in: ./data/testnet")
    logger.info("")
    
    # Initialize blockchain
    logger.info("Initializing blockchain...")
    blockchain = Blockchain()
    
    # Initialize P2P network
    logger.info(f"Initializing node: {node_id}")
    p2p = P2PNetwork(
        node_id=node_id,
        listen_port=port,
        network_manager=network_manager
    )
    
    # Register HEARTBEAT handler
    async def handle_heartbeat(message):
        """Handle heartbeat messages from peers"""
        logger.debug(f"Received heartbeat from {message.sender_id}")
        # Heartbeat received, peer is alive - no action needed
        pass
    
    from src.p2p.message import MessageType
    p2p.register_message_handler(MessageType.HEARTBEAT, handle_heartbeat)
    
    # Initialize API REST
    logger.info("Initializing REST API...")
    api = GameAPI(blockchain)
    
    # Start API REST in a separate thread
    api_port = network_info.get('api_port', 18080)
    logger.info(f"Starting REST API on port {api_port}...")
    
    def run_api():
        api.run(host='0.0.0.0', port=api_port, debug=False)
    
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Start P2P network
    logger.info("Starting P2P network...")
    await p2p.start()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Testnet node started successfully!")
    logger.info("=" * 60)
    logger.info(f"  Node ID: {node_id}")
    logger.info(f"  Network: {p2p.network_id}")
    logger.info(f"  P2P Port: {p2p.listen_port}")
    logger.info(f"  API Port: {api_port}")
    logger.info("")
    logger.info("🌐 Services running:")
    logger.info(f"  ✓ P2P Network: localhost:{p2p.listen_port}")
    logger.info(f"  ✓ REST API: http://localhost:{api_port}")
    logger.info("")
    logger.info("Press Ctrl+C to stop the node")
    logger.info("=" * 60)
    logger.info("")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
            
            # Periodically log stats
            if int(asyncio.get_event_loop().time()) % 60 == 0:
                stats = p2p.get_network_stats()
                logger.info(f"Stats: {stats['peer_count']} peers, "
                          f"{stats['active_connections']} connections")
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Shutting down testnet node...")
        await p2p.stop()
        logger.info("✓ Node stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Start a PlayerGold testnet node',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_testnet_node.py
  python scripts/start_testnet_node.py --node-id my_test_node
  python scripts/start_testnet_node.py --node-id node1 --port 19000
        """
    )
    
    parser.add_argument(
        '--node-id',
        type=str,
        default='testnet_node_1',
        help='Unique identifier for this node (default: testnet_node_1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to listen on (default: 18333 for testnet)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--validator',
        action='store_true',
        help='Run as validator node'
    )
    
    parser.add_argument(
        '--genesis-file',
        type=str,
        help='Genesis block file path'
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(start_testnet_node(
            args.node_id, 
            args.port, 
            args.config, 
            args.validator, 
            args.genesis_file
        ))
    except Exception as e:
        logger.error(f"Error starting testnet node: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
